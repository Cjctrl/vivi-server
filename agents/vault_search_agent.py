"""
KB Search Agent — semantic + full-text search over the NEXUS knowledge base.

All search operations go through AgentMemoryClient → NEXUS HTTP server.
No direct Qdrant access; no direct file I/O.
"""

from __future__ import annotations

import structlog
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from core.base_agent import BaseAgent
from core.confidence import hits_confidence
from memory.nexus.nexus_memory_bridge import (
    AgentMemoryClient,
    NexusUnavailableError,
    get_memory_client,
)

logger = structlog.get_logger(__name__).bind(component="vault_search_agent")


@dataclass
class SearchHit:
    title: str
    body: str
    tags: List[str]
    score: float
    match: str  # "semantic" | "fulltext"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "body": self.body[:500],
            "tags": self.tags,
            "score": self.score,
            "match": self.match,
        }


class VaultSearchAgent(BaseAgent):
    """
    Semantic + full-text search over the NEXUS knowledge base.

    Delegates all indexing and retrieval to the NEXUS HTTP server.
    The agent name is preserved for router compatibility.
    """

    name = "vault_search_agent"

    def __init__(self, client: Optional[AgentMemoryClient] = None) -> None:
        self._client = client or get_memory_client()

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        query: str = arguments.get("query", "").strip()
        if not query:
            return {"status": "error", "error": "No query provided", "confidence": 0.0}

        limit: int = int(arguments.get("limit", 5))
        semantic: bool = bool(arguments.get("semantic", True))
        fulltext: bool = bool(arguments.get("fulltext", True))

        try:
            raw_hits = self._client.search(
                query=query,
                limit=limit,
                semantic=semantic,
                fulltext=fulltext,
            )
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            logger.error("[vault_search_agent] search failed: %s", exc)
            return {"status": "error", "error": str(exc), "confidence": 0.0}

        hits = [
            SearchHit(
                title=h.get("title", ""),
                body=h.get("body", ""),
                tags=h.get("tags") or [],
                score=float(h.get("_score", 0.5)),
                match=h.get("_match", "unknown"),
            )
            for h in raw_hits
        ]

        top_title = hits[0].title if hits else "—"
        top_score = hits[0].score if hits else 0.0

        return {
            "status": "success",
            "query": query,
            "hits": [h.to_dict() for h in hits],
            "hit_count": len(hits),
            "summary": (
                f"Found {len(hits)} result(s) for '{query}'. "
                f"Top match: {top_title} (score: {top_score:.2f})"
            ),
            "confidence": hits_confidence([h.to_dict() for h in hits]),
            "error": None,
        }
