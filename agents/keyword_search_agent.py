"""
Keyword Search Agent — TF-IDF-inspired local file search with stop-word filtering.
Replaces local_file_search.py.
"""

from __future__ import annotations

import structlog
import math
from pathlib import Path
from typing import Any, Dict, List, Optional

from config.settings import KEYWORD_SEARCH_MAX_BYTES, NEXUS_KB_PATH
from core.base_agent import BaseAgent
from core.confidence import hits_confidence

logger = structlog.get_logger(__name__).bind(component="keyword_search_agent")

_MAX_FILE_BYTES = KEYWORD_SEARCH_MAX_BYTES  # 20 MB from settings
_BINARY_THRESHOLD = 0.20     # >20% non-printable → skip
_SNIPPET_WINDOW = 200
_SNIPPET_STEP = 50

_STOP_WORDS = frozenset({
    "the", "a", "an", "is", "in", "it", "of", "to", "and", "or", "for",
    "with", "on", "at", "by", "this", "that", "be", "are", "was", "were",
    "has", "have", "had", "not", "from", "as", "but", "if", "so", "do",
    "did", "can", "will", "would", "should", "could", "about", "more",
    "some", "into", "up", "out", "just", "also", "then", "when", "what",
    "how", "which", "there", "their", "they", "we", "our", "my", "your",
    "you", "he", "she", "his", "her", "its", "them", "him", "us", "all",
    "any", "each", "both", "between", "through", "after", "before", "same",
    "other", "than", "such", "only", "new", "first", "last", "most", "own",
    "no", "may", "let",
})

_DEFAULT_FILE_TYPES = [
    ".md", ".txt", ".py", ".json", ".yaml", ".yml",
    ".toml", ".cfg", ".ini",
]


class KeywordSearchAgent(BaseAgent):
    """Searches local files for query terms using TF-IDF-inspired scoring."""

    name = "keyword_search_agent"

    def execute(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        query: str = (arguments.get("query") or arguments.get("task") or "").strip()
        if not query:
            return {"status": "error", "error": "No query provided", "confidence": 0.0}

        search_path = Path(arguments.get("search_path") or NEXUS_KB_PATH or "./")
        file_types: List[str] = arguments.get("file_types") or _DEFAULT_FILE_TYPES
        max_results: int = int(arguments.get("max_results", 10))

        hits = self._search_files(query, search_path, file_types, max_results)

        return {
            "status": "success",
            "query": query,
            "hits": hits,
            "hit_count": len(hits),
            "summary": (
                f"Found {len(hits)} file(s) matching '{query}'. "
                + (f"Top match: {hits[0]['file']}" if hits else "No results.")
            ),
            "confidence": hits_confidence(hits),
            "error": None,
        }

    # ------------------------------------------------------------------

    def _search_files(
        self,
        query: str,
        search_path: Path,
        file_types: List[str],
        max_results: int,
    ) -> List[Dict[str, Any]]:
        raw_terms = [t.lower() for t in query.split() if t]
        filtered_terms = [t for t in raw_terms if t not in _STOP_WORDS and len(t) > 1]
        if not filtered_terms:
            filtered_terms = raw_terms  # fallback: use all terms

        hits: List[Dict[str, Any]] = []

        for path in search_path.rglob("*"):
            if not path.is_file():
                continue
            if path.suffix.lower() not in file_types:
                continue

            try:
                stat = path.stat()
            except OSError:
                continue

            if stat.st_size > _MAX_FILE_BYTES:
                logger.debug("[keyword_search] skipping large file: %s", path)
                continue

            try:
                text = path.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                logger.debug("keyword_search_skip_file", exc_info=True)
                continue

            if _is_binary(text):
                continue

            text_lower = text.lower()
            score = _tfidf_score(text_lower, filtered_terms)
            if score <= 0:
                continue

            snippet = _best_snippet(text, text_lower, filtered_terms)
            hits.append({"file": str(path), "snippet": snippet, "score": float(score)})

        hits.sort(key=lambda x: x["score"], reverse=True)
        return hits[:max_results]


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _is_binary(text: str) -> bool:
    if not text:
        return False
    non_printable = sum(1 for c in text if not c.isprintable() and c not in "\n\r\t")
    return (non_printable / len(text)) > _BINARY_THRESHOLD


def _tfidf_score(text_lower: str, terms: List[str]) -> float:
    total = 0.0
    n_terms = max(1, len(terms))
    for term in terms:
        count = text_lower.count(term)
        if count > 0:
            total += count * math.log(1 + 1 / (0.1 + count / n_terms))
    return total


def _best_snippet(text: str, text_lower: str, terms: List[str]) -> str:
    if not text:
        return ""

    best_start = 0
    best_score = -1

    for start in range(0, len(text) - _SNIPPET_WINDOW + 1, _SNIPPET_STEP):
        window = text_lower[start : start + _SNIPPET_WINDOW]
        score = sum(window.count(term) for term in terms)
        if score > best_score:
            best_score = score
            best_start = start

    # If no terms found at all, fall back to first N chars
    if best_score <= 0:
        for term in terms:
            idx = text_lower.find(term)
            if idx != -1:
                best_start = max(0, idx - 60)
                break

    snippet = text[best_start : best_start + _SNIPPET_WINDOW].strip().replace("\n", " ")
    return snippet
