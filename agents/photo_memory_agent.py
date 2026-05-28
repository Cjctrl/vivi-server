"""
Photo Memory Agent — persistent image memory backed by Qdrant.

Collection: "photo_memory"
Embedding:  nomic-embed-text via EmbeddingService (same as memory_agent)
Cache:      LRU OrderedDict, 50 entries, 5-minute TTL
"""

from __future__ import annotations

import structlog
import time
import uuid
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from qdrant_client.http.models import PointStruct

from config.settings import (
    PHOTO_MEMORY_CACHE_SIZE,
    PHOTO_MEMORY_CACHE_TTL,
    VECTOR_DIMENSION,
)
from core.base_agent import BaseAgent
from core.vector_store import EmbeddingService, VectorStore, get_vector_store

logger = structlog.get_logger(__name__).bind(component="photo_memory_agent")

_COLLECTION = "photo_memory"
_UUID_NS    = uuid.NAMESPACE_DNS


class PhotoMemoryAgent(BaseAgent):
    """
    Store and recall images semantically.

    Actions:
        store   — embed description + upsert into Qdrant
        recall  — semantic search, returns top-k entries
        list    — N most recent entries (no vectors)
        delete  — remove entry by ID
        stats   — total count, most recalled
    """

    name = "photo_memory_agent"

    # LRU recall cache: key = query string, value = (result_list, timestamp)
    _recall_cache: OrderedDict[str, tuple[List[Dict], float]] = OrderedDict()
    _cache_lock_flag = False  # simple flag — not thread-safe but acceptable for cache

    def __init__(self) -> None:
        self._store: VectorStore = get_vector_store()
        self._embedder = EmbeddingService()
        self._store.ensure_collection(_COLLECTION, VECTOR_DIMENSION)
        self._prewarm()

    # ------------------------------------------------------------------
    # Dispatch
    # ------------------------------------------------------------------

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action: str = str(arguments.get("action", "recall")).lower()
        dispatch = {
            "store":  self._store_memory,
            "recall": self._recall_memory,
            "list":   self._list_memories,
            "delete": self._delete_memory,
            "stats":  self._stats,
        }
        handler = dispatch.get(action)
        if handler is None:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: store, recall, list, delete, stats.",
                "confidence": 0.0,
            }
        return handler(arguments)

    # ------------------------------------------------------------------
    # Store
    # ------------------------------------------------------------------

    def _store_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        description: str = str(args.get("description", "")).strip()
        if not description:
            return {"status": "error", "error": "description is required for store.", "confidence": 0.0}

        image_path: str  = str(args.get("image_path", ""))
        ocr_text:   Optional[str] = args.get("ocr_text")
        tags:       List[str]    = list(args.get("tags", []))
        file_hash:  str  = str(args.get("file_hash", ""))

        # Deduplicate by file_hash
        if file_hash:
            existing = self._find_by_hash(file_hash)
            if existing:
                self._update_metadata(existing["id"], {"description": description, "ocr_text": ocr_text})
                return {
                    "status":    "success",
                    "memory_id": existing["id"],
                    "duplicate": True,
                    "confidence": 1.0,
                    "error":     None,
                }

        try:
            vector = self._embedder.embed(description)
        except Exception as exc:
            return {"status": "error", "error": f"Embedding failed: {exc}", "confidence": 0.0}

        memory_id = str(uuid.uuid5(_UUID_NS, f"{file_hash}:{description[:80]}:{time.time()}"))
        payload: Dict[str, Any] = {
            "image_path":    image_path,
            "description":   description,
            "ocr_text":      ocr_text or "",
            "tags":          tags,
            "file_hash":     file_hash,
            "created_at":    datetime.now(timezone.utc).isoformat(),
            "times_recalled": 0,
            "last_recalled": None,
        }

        try:
            self._store.upsert_points(
                _COLLECTION,
                [PointStruct(id=memory_id, vector=vector, payload=payload)],
            )
        except Exception as exc:
            return {"status": "error", "error": f"Upsert failed: {exc}", "confidence": 0.0}

        logger.debug("[photo_memory] stored id=%s path=%s", memory_id, image_path)
        return {
            "status":    "success",
            "memory_id": memory_id,
            "duplicate": False,
            "confidence": 1.0,
            "error":     None,
        }

    # ------------------------------------------------------------------
    # Recall
    # ------------------------------------------------------------------

    def _recall_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query: str = str(args.get("query", "")).strip()
        if not query:
            return {"status": "error", "error": "query is required for recall.", "confidence": 0.0}

        limit: int   = int(args.get("limit", 5))
        min_score    = float(args.get("min_score", 0.3))

        # LRU cache hit
        cache_key = f"{query}:{limit}:{min_score}"
        hit = self._cache_get(cache_key)
        if hit is not None:
            logger.debug("[photo_memory] cache hit for query=%s", query[:40])
            return {
                "status":   "success",
                "memories": hit,
                "count":    len(hit),
                "cached":   True,
                "confidence": 0.85,
                "error":    None,
            }

        try:
            vector = self._embedder.embed(query)
        except Exception as exc:
            return {"status": "error", "error": f"Query embedding failed: {exc}", "confidence": 0.0}

        try:
            results = self._store.search(_COLLECTION, vector, limit=limit, score_threshold=min_score)
        except Exception as exc:
            return {"status": "error", "error": f"Search failed: {exc}", "confidence": 0.0}

        memories: List[Dict[str, Any]] = []
        for pt in results:
            payload = pt.payload or {}
            memories.append({
                "id":          str(pt.id),
                "image_path":  payload.get("image_path", ""),
                "description": payload.get("description", ""),
                "ocr_text":    payload.get("ocr_text", ""),
                "tags":        payload.get("tags", []),
                "created_at":  payload.get("created_at", ""),
                "times_recalled": int(payload.get("times_recalled", 0)),
                "score":       round(float(pt.score), 4),
            })
            # Increment recall counter asynchronously (best-effort)
            self._increment_recall(str(pt.id), payload)

        self._cache_set(cache_key, memories)

        return {
            "status":   "success",
            "memories": memories,
            "count":    len(memories),
            "cached":   False,
            "confidence": 0.85 if memories else 0.0,
            "error":    None,
        }

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    def _list_memories(self, args: Dict[str, Any]) -> Dict[str, Any]:
        limit = int(args.get("limit", 20))
        try:
            # Qdrant scroll — get recent entries (no vector needed)
            scroll_result, _ = self._store.client.scroll(
                collection_name=_COLLECTION,
                limit=limit,
                with_payload=True,
                with_vectors=False,
            )
        except Exception as exc:
            return {"status": "error", "error": f"List failed: {exc}", "confidence": 0.0}

        entries = []
        for pt in scroll_result:
            payload = pt.payload or {}
            entries.append({
                "id":          str(pt.id),
                "image_path":  payload.get("image_path", ""),
                "description": payload.get("description", ""),
                "tags":        payload.get("tags", []),
                "created_at":  payload.get("created_at", ""),
                "times_recalled": int(payload.get("times_recalled", 0)),
            })

        # Sort by created_at descending (most recent first)
        entries.sort(key=lambda e: e["created_at"], reverse=True)

        return {
            "status":   "success",
            "entries":  entries,
            "count":    len(entries),
            "confidence": 1.0,
            "error":    None,
        }

    # ------------------------------------------------------------------
    # Delete
    # ------------------------------------------------------------------

    def _delete_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        memory_id = str(args.get("id", "")).strip()
        if not memory_id:
            return {"status": "error", "error": "id is required for delete.", "confidence": 0.0}
        try:
            self._store.client.delete(
                collection_name=_COLLECTION,
                points_selector=[memory_id],
            )
        except Exception as exc:
            return {"status": "error", "error": f"Delete failed: {exc}", "confidence": 0.0}

        # Invalidate cache entries that might include this ID
        self._cache_clear()

        return {"status": "success", "deleted_id": memory_id, "confidence": 1.0, "error": None}

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def _stats(self, _args: Dict[str, Any]) -> Dict[str, Any]:
        total = self._store.count(_COLLECTION)
        try:
            scroll_result, _ = self._store.client.scroll(
                collection_name=_COLLECTION,
                limit=200,
                with_payload=True,
                with_vectors=False,
            )
            entries = [(pt.payload or {}) for pt in scroll_result]
            most_recalled = max(entries, key=lambda e: e.get("times_recalled", 0), default={})
        except Exception:
            most_recalled = {}

        return {
            "status":        "success",
            "total":         total,
            "cache_entries": len(self._recall_cache),
            "most_recalled_description": most_recalled.get("description", ""),
            "most_recalled_count":       most_recalled.get("times_recalled", 0),
            "confidence":    1.0,
            "error":         None,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _find_by_hash(self, file_hash: str) -> Optional[Dict]:
        try:
            from qdrant_client.models import Filter, FieldCondition, MatchValue
            result = self._store.client.scroll(
                collection_name=_COLLECTION,
                scroll_filter=Filter(
                    must=[FieldCondition(key="file_hash", match=MatchValue(value=file_hash))]
                ),
                limit=1,
                with_payload=True,
                with_vectors=False,
            )
            pts = result[0]
            if pts:
                return {"id": str(pts[0].id), **( pts[0].payload or {})}
        except Exception:
            pass
        return None

    def _update_metadata(self, point_id: str, updates: Dict[str, Any]) -> None:
        try:
            self._store.client.set_payload(
                collection_name=_COLLECTION,
                payload={k: v for k, v in updates.items() if v is not None},
                points=[point_id],
            )
        except Exception as exc:
            logger.debug("[photo_memory] metadata update failed: %s", exc)

    def _increment_recall(self, point_id: str, payload: Dict[str, Any]) -> None:
        try:
            new_count = int(payload.get("times_recalled", 0)) + 1
            self._store.client.set_payload(
                collection_name=_COLLECTION,
                payload={
                    "times_recalled": new_count,
                    "last_recalled":  datetime.now(timezone.utc).isoformat(),
                },
                points=[point_id],
            )
        except Exception:
            pass

    # ------------------------------------------------------------------
    # LRU cache helpers
    # ------------------------------------------------------------------

    def _cache_get(self, key: str) -> Optional[List[Dict]]:
        entry = self._recall_cache.get(key)
        if entry is None:
            return None
        data, ts = entry
        if time.monotonic() - ts > PHOTO_MEMORY_CACHE_TTL:
            del self._recall_cache[key]
            return None
        self._recall_cache.move_to_end(key)
        return data

    def _cache_set(self, key: str, data: List[Dict]) -> None:
        self._recall_cache[key] = (data, time.monotonic())
        self._recall_cache.move_to_end(key)
        while len(self._recall_cache) > PHOTO_MEMORY_CACHE_SIZE:
            self._recall_cache.popitem(last=False)

    def _cache_clear(self) -> None:
        self._recall_cache.clear()

    # ------------------------------------------------------------------
    # Pre-warm: load top-10 most recalled into cache
    # ------------------------------------------------------------------

    def _prewarm(self) -> None:
        try:
            scroll_result, _ = self._store.client.scroll(
                collection_name=_COLLECTION,
                limit=100,
                with_payload=True,
                with_vectors=False,
            )
            entries = sorted(
                scroll_result,
                key=lambda pt: (pt.payload or {}).get("times_recalled", 0),
                reverse=True,
            )[:10]

            for pt in entries:
                payload = pt.payload or {}
                desc = payload.get("description", "")
                if desc:
                    key = f"{desc[:40]}:5:0.3"
                    self._cache_set(key, [{
                        "id":          str(pt.id),
                        "image_path":  payload.get("image_path", ""),
                        "description": desc,
                        "ocr_text":    payload.get("ocr_text", ""),
                        "tags":        payload.get("tags", []),
                        "created_at":  payload.get("created_at", ""),
                        "times_recalled": int(payload.get("times_recalled", 0)),
                        "score":       1.0,
                    }])
            logger.debug("[photo_memory] pre-warmed %d entries", len(entries))
        except Exception as exc:
            logger.debug("[photo_memory] pre-warm skipped: %s", exc)
