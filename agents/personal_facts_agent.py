"""
Personal Facts Agent — cross-session user profile memory.

Stores durable personal facts extracted from conversation (name, relationships,
preferences, habits, important dates) in a single persistent NEXUS node.
Unlike MemoryAgent (ephemeral per-session), this node is never auto-cleared.

Actions:
    extract_and_store — LLM-extract personal facts from raw user text, then persist
    recall_relevant   — semantic search for facts relevant to a query
    get_all           — return the full facts node body
"""

from __future__ import annotations

import json
import structlog
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config.settings import CONDUCTOR_MODEL
from core.base_agent import BaseAgent
from core.llm_client import LLMClient
try:
    from memory.nexus.nexus_memory_bridge import (
        AgentMemoryClient,
        NexusAPIError,
        NexusUnavailableError,
        get_memory_client,
    )
    _NEXUS_BRIDGE_AVAILABLE = True
except ImportError:
    AgentMemoryClient = None  # type: ignore[assignment,misc]
    NexusAPIError = Exception  # type: ignore[assignment,misc]
    NexusUnavailableError = Exception  # type: ignore[assignment,misc]
    get_memory_client = None  # type: ignore[assignment]
    _NEXUS_BRIDGE_AVAILABLE = False

logger = structlog.get_logger(__name__).bind(component="personal_facts_agent")

_FACTS_NODE = "user_profile/personal_facts"
_FACTS_TAGS = ["user_profile", "personal_facts", "persistent"]

_EXTRACTION_SYSTEM = (
    "You extract durable personal facts from user messages. "
    "Return ONLY a JSON array. "
    "A personal fact is a stable truth about the user: name, family members, "
    "preferences, habits, routines, important dates, health details, work context. "
    "Do NOT extract task requests, questions, or temporary state. "
    'Each fact: {"fact": "<short statement>", "category": "<family|preference|habit|date|work|health|other>"}. '
    "Return [] if nothing qualifies."
)


class PersonalFactsAgent(BaseAgent):
    """
    Store and retrieve permanent personal facts about the user.
    Mirrors MemoryAgent's pattern but writes to a single cross-session node.
    """

    name = "personal_facts"

    def __init__(self, client: Optional["AgentMemoryClient"] = None) -> None:
        if _NEXUS_BRIDGE_AVAILABLE:
            self._client = client or get_memory_client()
        else:
            self._client = None
        self._llm = LLMClient()

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        if not _NEXUS_BRIDGE_AVAILABLE:
            return {
                "status": "error",
                "error": "Nexus memory bridge not available in this build",
                "confidence": 0.0,
            }

        action: str = arguments.get("action", "recall_relevant").lower()

        if action == "extract_and_store":
            return self._extract_and_store(arguments)
        elif action == "recall_relevant":
            return self._recall_relevant(arguments)
        elif action == "get_all":
            return self._get_all()
        else:
            return {
                "status": "error",
                "error": f"Unknown action '{action}'. Use: extract_and_store, recall_relevant, get_all.",
                "confidence": 0.0,
            }

    # ──────────────────────────────────────────────────────────────────────────

    def _extract_and_store(self, args: Dict[str, Any]) -> Dict[str, Any]:
        text: str = str(args.get("text", "")).strip()
        if not text:
            return {"status": "error", "error": "text is required", "confidence": 0.0}

        # LLM fact extraction
        try:
            raw = self._llm.chat_json(
                model=CONDUCTOR_MODEL,
                messages=[
                    {"role": "system", "content": _EXTRACTION_SYSTEM},
                    {"role": "user", "content": text},
                ],
                fallback=[],
            )
        except Exception as exc:
            logger.warning("PersonalFactsAgent: LLM extraction failed: %s", exc)
            return {"status": "error", "error": f"Extraction failed: {exc}", "confidence": 0.0}

        facts: List[Dict[str, str]] = []
        if isinstance(raw, list):
            facts = [f for f in raw if isinstance(f, dict) and "fact" in f]
        elif isinstance(raw, dict) and "facts" in raw:
            facts = raw["facts"]

        if not facts:
            return {"status": "success", "stored": 0, "facts": [], "error": None, "confidence": 0.8}

        # Persist each fact as an appended entry
        timestamp = datetime.now(timezone.utc).isoformat()
        stored_count = 0
        try:
            existing = self._client.get_node(_FACTS_NODE)
            for item in facts:
                fact_text = item.get("fact", "").strip()
                category  = item.get("category", "other").strip()
                if not fact_text:
                    continue
                entry = f"**[{category}]** {timestamp}\n{fact_text}\n"
                if existing is None:
                    self._client.create_node(
                        title=_FACTS_NODE,
                        body=entry,
                        tags=_FACTS_TAGS,
                        node_type="memory",
                    )
                    existing = True  # subsequent facts append
                else:
                    self._client.append(title=_FACTS_NODE, text=entry)
                stored_count += 1
                logger.info("PersonalFactsAgent: stored fact [%s] %r", category, fact_text[:60])
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            return {"status": "error", "error": f"Store failed: {exc}", "confidence": 0.0}

        return {
            "status": "success",
            "stored": stored_count,
            "facts": [f.get("fact", "") for f in facts],
            "error": None,
            "confidence": 1.0,
        }

    def _recall_relevant(self, args: Dict[str, Any]) -> Dict[str, Any]:
        query: str = str(args.get("query", "")).strip()
        limit: int = int(args.get("limit", 5))

        if not query:
            return {"status": "error", "error": "query is required", "confidence": 0.0}

        try:
            results = self._client.search(query=query, limit=limit * 3, semantic=True, fulltext=True)
            # Filter to user_profile nodes only
            results = [
                r for r in results
                if "user_profile" in (r.get("tags") or [])
            ][:limit]
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            return {"status": "error", "error": f"Recall failed: {exc}", "confidence": 0.0}

        facts = [r.get("body", "") or r.get("content", "") for r in results if r]
        # Parse individual fact lines from the body text
        fact_lines: List[str] = []
        for body in facts:
            for line in body.splitlines():
                line = line.strip()
                # Skip metadata lines (bold category headers)
                if line and not line.startswith("**["):
                    fact_lines.append(line)

        return {
            "status": "success",
            "facts": fact_lines[:limit],
            "count": len(fact_lines[:limit]),
            "error": None,
            "confidence": 0.8 if fact_lines else 0.3,
        }

    def _get_all(self) -> Dict[str, Any]:
        try:
            node = self._client.get_node(_FACTS_NODE)
        except NexusUnavailableError as exc:
            return {"status": "error", "error": str(exc), "confidence": 0.0}
        except Exception as exc:
            return {"status": "error", "error": f"Get failed: {exc}", "confidence": 0.0}

        if node is None:
            return {"status": "success", "body": "", "count": 0, "error": None, "confidence": 0.5}

        body = node.get("body", "") or ""
        lines = [l.strip() for l in body.splitlines() if l.strip() and not l.strip().startswith("**[")]
        return {
            "status": "success",
            "body": body,
            "facts": lines,
            "count": len(lines),
            "error": None,
            "confidence": 1.0,
        }
