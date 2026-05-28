"""
memory/nexus/world_model.py
Layer 2 of Memory V2 — the World Model.

Tracks entities and the facts attached to them, distilled from everything the
user mentions or V.I.V.I observes. Unlike the identity model (which is about the
user) this is about the *world* the user operates in: their projects, tools,
people, machines, deadlines.

Storage is a dedicated Qdrant collection ("world_model", 768-dim, same embed
model as nexus_kb) added to the shared VectorStore singleton. One point per
entity, keyed by a deterministic UUID derived from the entity name, so repeated
observations of the same entity merge in place rather than piling up duplicates.

Like the identity layer, observe() is best-effort: the conductor calls it
fire-and-forget and it must never raise into or block a task.
"""

from __future__ import annotations

import logging
import threading
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.settings import CONDUCTOR_MODEL, VECTOR_DIMENSION
from core.llm_client import LLMClient
from core.vector_store import get_embedding_service, get_vector_store

logger = logging.getLogger(__name__)

WORLD_COLLECTION = "world_model"
_UUID_NS = uuid.NAMESPACE_DNS

_EXTRACTION_SYSTEM = (
    "You extract entities and facts about them from text. An entity is a "
    "concrete, nameable thing: a project, person, tool, library, machine, "
    "organization, file, or place. Return ONLY a JSON array; each item is "
    '{"entity": "<canonical name>", "type": "<project|person|tool|org|place|'
    'concept|other>", "fact": "<one short factual statement about the entity>"}. '
    "Emit one array element per (entity, fact) pair. Skip vague pronouns and "
    "transient task phrasing. Return [] if nothing concrete is present."
)


def _entity_point_id(entity_name: str) -> str:
    """Deterministic point id for an entity, so re-observation upserts in place."""
    return str(uuid.uuid5(_UUID_NS, f"world:{entity_name.strip().lower()}"))


class WorldModel:
    """Entity/fact memory backed by a dedicated Qdrant collection.

    Constructor dependencies are injectable (store / embedder / llm) purely so
    tests can run against a throwaway Qdrant path and a fake embedder without
    touching the real singletons or Ollama.
    """

    def __init__(self, store: Any = None, embedder: Any = None, llm: Any = None) -> None:
        self._store = store if store is not None else get_vector_store()
        self._embedder = embedder if embedder is not None else get_embedding_service()
        self._llm = llm if llm is not None else LLMClient()
        self._lock = threading.Lock()
        self._collection_ready = False

    def _ensure_collection(self) -> None:
        if not self._collection_ready:
            self._store.ensure_collection(WORLD_COLLECTION, VECTOR_DIMENSION)
            self._collection_ready = True

    # ------------------------------------------------------------------
    # Write
    # ------------------------------------------------------------------

    def observe(self, text: str) -> int:
        """Extract (entity, fact) pairs from *text* and upsert them.

        Returns the number of entities written (0 on any failure or empty
        input). Never raises — callers fire this in the background.
        """
        text = (text or "").strip()
        if not text:
            return 0

        try:
            pairs = self._extract_pairs(text)
        except Exception as exc:
            logger.debug("[world] extraction failed (ignored): %s", exc)
            return 0
        if not pairs:
            return 0

        # Group facts by entity so multiple facts about the same entity in one
        # observation collapse into a single upsert.
        grouped: Dict[str, Dict[str, Any]] = {}
        for item in pairs:
            if not isinstance(item, dict):
                continue
            entity = str(item.get("entity", "")).strip()
            fact = str(item.get("fact", "")).strip()
            if not entity or not fact:
                continue
            etype = str(item.get("type", "other")).strip() or "other"
            bucket = grouped.setdefault(entity, {"type": etype, "facts": []})
            if fact not in bucket["facts"]:
                bucket["facts"].append(fact)

        if not grouped:
            return 0

        written = 0
        try:
            self._ensure_collection()
            for entity, info in grouped.items():
                if self._upsert_entity(entity, info["type"], info["facts"]):
                    written += 1
        except Exception as exc:
            logger.debug("[world] upsert failed (ignored): %s", exc)
        return written

    def _extract_pairs(self, text: str) -> List[Dict[str, Any]]:
        raw = self._llm.chat_json(
            model=CONDUCTOR_MODEL,
            messages=[
                {"role": "system", "content": _EXTRACTION_SYSTEM},
                {"role": "user", "content": text},
            ],
            fallback=[],
        )
        if isinstance(raw, list):
            return raw
        if isinstance(raw, dict) and isinstance(raw.get("entities"), list):
            return raw["entities"]
        return []

    def _upsert_entity(self, entity: str, entity_type: str, new_facts: List[str]) -> bool:
        """Merge *new_facts* into the stored entity (dedup) and re-embed. Lock-guarded."""
        from qdrant_client.http.models import PointStruct

        point_id = _entity_point_id(entity)
        with self._lock:
            existing = self._store.get_point(WORLD_COLLECTION, point_id)
            facts: List[str] = []
            confidence = 0.5
            entity_name = entity
            etype = entity_type
            if existing is not None and getattr(existing, "payload", None):
                payload = existing.payload or {}
                facts = list(payload.get("facts") or [])
                entity_name = payload.get("entity_name", entity)
                etype = payload.get("entity_type", entity_type) or entity_type
                try:
                    confidence = float(payload.get("confidence", 0.5))
                except (TypeError, ValueError):
                    confidence = 0.5

            # Dedup append — preserve order, ignore facts we already hold.
            added = False
            for fact in new_facts:
                if fact not in facts:
                    facts.append(fact)
                    added = True

            # Re-observing an entity (even with no new fact) reinforces confidence.
            confidence = round(min(1.0, confidence + 0.1), 4)

            # Embed entity name + facts so search matches both the name and its
            # attached facts.
            embed_text = f"{entity_name}: " + " ".join(facts)
            vector = self._embedder.embed(embed_text)

            payload = {
                "entity_name": entity_name,
                "entity_type": etype,
                "facts": facts,
                "last_seen": datetime.now(timezone.utc).isoformat(),
                "confidence": confidence,
            }
            self._store.upsert_points(
                WORLD_COLLECTION,
                [PointStruct(id=point_id, vector=vector, payload=payload)],
            )
            return added or existing is None

    # ------------------------------------------------------------------
    # Read
    # ------------------------------------------------------------------

    def query(self, question: str, limit: int = 5) -> List[Dict[str, Any]]:
        """Semantic search over the world model; returns up to *limit* entities."""
        question = (question or "").strip()
        if not question:
            return []
        try:
            self._ensure_collection()
            vector = self._embedder.embed(question)
            hits = self._search(vector, limit)
        except Exception as exc:
            logger.debug("[world] query failed (ignored): %s", exc)
            return []

        results: List[Dict[str, Any]] = []
        for hit in hits:
            payload = dict(getattr(hit, "payload", None) or {})
            payload["_score"] = float(getattr(hit, "score", 0.0))
            results.append(payload)
        return results

    def _search(self, vector: List[float], limit: int) -> List[Any]:
        """Query the collection, tolerating the qdrant-client vector-kwarg rename.

        Newer qdrant-client uses ``query=``; older uses ``query_vector=``. The
        shared VectorStore.search tries them in the opposite order, so we query
        the client directly here to stay robust across versions.
        """
        try:
            return self._store.client.query_points(
                collection_name=WORLD_COLLECTION,
                query=vector,
                limit=limit,
                with_payload=True,
            ).points
        except TypeError:
            return self._store.client.query_points(
                collection_name=WORLD_COLLECTION,
                query_vector=vector,
                limit=limit,
                with_payload=True,
            ).points


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

_world_model: Optional[WorldModel] = None
_singleton_lock = threading.Lock()


def get_world_model() -> WorldModel:
    """Return the process-wide WorldModel singleton."""
    global _world_model
    if _world_model is None:
        with _singleton_lock:
            if _world_model is None:
                _world_model = WorldModel()
    return _world_model
