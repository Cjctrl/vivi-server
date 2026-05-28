"""
Memory Agent — cross-turn episodic memory via the NEXUS knowledge base.

Memories are stored as .md nodes under 'memories/session_{session_id}'.
Each session gets one node; subsequent stores append to it.
All operations go through AgentMemoryClient; no direct Qdrant access.
"""

from __future__ import annotations

import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from core.base_agent import BaseAgent
from core.confidence import hits_confidence
from memory.nexus.nexus_memory_bridge import (
    AgentMemoryClient,
    NexusAPIError,
    NexusUnavailableError,
    get_memory_client,
)

logger = structlog.get_logger(__name__).bind(component="memory_agent")

_COLLECTION = "memories"


class MemoryAgent(BaseAgent):
    """
    Store and recall conversational memories across turns.

    Actions:
        store  — persist a memory entry for a session
        recall — find relevant memories by semantic search
        clear  — delete the session memory node
    """

    name = "memory_agent"

    def __init__(self, client: Optional[AgentMemoryClient] = None) -> None:
        self._client = client or get_memory_client()

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        action: str = arguments.get("action", "recall").lower()

        if action == "store":
            return self._store_memory(arguments)
        elif action == "recall":
            return self._recall_memory(arguments)
        elif action == "clear":
            return self._clear_session(arguments)
        else:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: store, recall, clear.",
                "confidence": 0.0,
            }

    # ──────────────────────────────────────────────────────────────────────────

    def _session_title(self, session_id: str) -> str:
        return f"{_COLLECTION}/session_{session_id}"

    def _store_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_id: str = str(args.get("session_id", "default")).strip()
        content: Any = args.get("content", "")
        key: str = str(args.get("key", ""))
        turn: int = int(args.get("turn", 0))
        tags: List[str] = args.get("tags") or []
        node_type: str = str(args.get("node_type", "observation"))

        if not content:
            return {"status": "error", "error": "content is required for store", "confidence": 0.0}

        content_str = str(content) if not isinstance(content, str) else content
        timestamp = datetime.now(timezone.utc).isoformat()
        entry = f"**[turn {turn}]** {timestamp}  \n{content_str}"
        if key:
            entry = f"**[{key} · turn {turn}]** {timestamp}  \n{content_str}"

        title = self._session_title(session_id)
        node_tags = list(set(["memory", f"session:{session_id}", node_type] + tags))

        try:
            existing = self._client.get_node(title)
            if existing is None:
                # First memory for this session — create the node
                self._client.create_node(
                    title=title,
                    body=entry,
                    tags=node_tags,
                    node_type="memory",
                )
            else:
                # Subsequent memory — append to the existing node
                self._client.append(title=title, text=entry)
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            return {"status": "error", "error": f"Store failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "stored": True,
            "title": title,
            "session_id": session_id,
            "confidence": 1.0,
            "error": None,
        }

    def _recall_memory(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query: str = str(args.get("query", "")).strip()
        if not query:
            return {"status": "error", "error": "query is required for recall", "confidence": 0.0}

        session_id: Optional[str] = args.get("session_id")
        limit: int = int(args.get("limit", 5))

        try:
            if session_id:
                # Targeted: search within one session node first
                title = self._session_title(session_id)
                node = self._client.get_node(title)
                if node:
                    # Do a broad search filtered to memory nodes
                    results = self._client.search(
                        query=query, limit=limit * 2, semantic=True, fulltext=True
                    )
                    # Filter to this session
                    results = [
                        r for r in results
                        if f"session:{session_id}" in (r.get("tags") or [])
                    ][:limit]
                else:
                    results = []
            else:
                # Global memory search across all sessions
                results = self._client.search(
                    query=query, limit=limit * 2, semantic=True, fulltext=True
                )
                # Filter to memory-type nodes only
                results = [
                    r for r in results
                    if "memory" in (r.get("tags") or []) or r.get("type") == "memory"
                ][:limit]
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            return {"status": "error", "error": f"Recall failed: {exc}", "confidence": 0.0}

        memories = [
            {
                "title": r.get("title", ""),
                "content": r.get("body", ""),
                "tags": r.get("tags") or [],
                "score": float(r.get("_score", 0.5)),
            }
            for r in results
        ]

        return {
            "status": "success",
            "memories": memories,
            "count": len(memories),
            "confidence": hits_confidence([{"score": m["score"]} for m in memories]),
            "error": None,
        }

    def _clear_session(self, args: Dict[str, Any]) -> Dict[str, Any]:
        session_id: str = str(args.get("session_id", "")).strip()
        if not session_id:
            return {
                "status": "error",
                "error": "session_id is required for clear",
                "confidence": 0.0,
            }

        title = self._session_title(session_id)
        try:
            self._client.delete_node(title)
        except NexusAPIError as exc:
            if "404" in str(exc):
                # Node didn't exist — treat as already cleared
                pass
            else:
                return {"status": "error", "error": str(exc), "confidence": 0.0}
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            return {"status": "error", "error": f"Clear failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "cleared": True,
            "session_id": session_id,
            "title": title,
            "confidence": 1.0,
            "error": None,
        }
