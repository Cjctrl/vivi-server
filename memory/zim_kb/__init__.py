"""
memory/zim_kb/ - ZIM-based offline knowledge retrieval.

Distinct from memory/nexus/ (the Qdrant-backed VIVI knowledge graph). This
package retrieves answers from ZIM archives stored on the memory disk
(VIVI_MEMDSK_PATH) via a Markdown hot cache, FTS5 full-text search, and
(when wired in) vector similarity search over chunk embeddings.

Public surface (re-exported here):
    query(text, ...)          - one-stop retrieval, fills cache on miss
    search(text, ...)          - cache-only FTS search (no ingest)
    mark_accessed(ids, ...)    - bump access counters + retrieval_log
    find_and_ingest(...)       - manually trigger ZIM -> cache for a query
    run_startup()              - run the spec startup sequence
    Hit                        - search result
    Domain                     - routing domains
    IngestionAttempt           - auto-ingest result detail

Submodules:
    db, catalog, startup, zim_source, converter, cache, retriever, auto_ingest
"""
from __future__ import annotations

import logging
from typing import Optional

from memory.zim_kb.auto_ingest import IngestionAttempt, find_and_ingest
from memory.zim_kb.catalog import Domain
from memory.zim_kb.retriever import Hit, mark_accessed, search
from memory.zim_kb.startup import StartupReport, run_startup

__all__ = [
    "query",
    "search",
    "mark_accessed",
    "find_and_ingest",
    "run_startup",
    "Hit",
    "Domain",
    "IngestionAttempt",
    "StartupReport",
]

logger = logging.getLogger(__name__)


def query(
    text: str,
    *,
    domain: Optional[Domain] = None,
    limit: int = 5,
    auto_ingest_on_miss: bool = True,
    mark_accessed_on_return: bool = True,
    prefer_images: bool = False,
    keep_images: bool = False,
) -> list[Hit]:
    """High-level retrieval. Cache-first; on miss, auto-ingest from ZIM and
    re-search. Returns up to `limit` hits ranked by RRF.

    - `domain` (optional) filters the cache search by archive tag AND scopes
      the auto-ingest's archive routing. If auto-ingest lands an article in
      a fallback archive (different tag), the re-search drops the domain
      filter so the freshly-cached article is still returned.
    - `auto_ingest_on_miss` (default True) controls the fallback. Set False
      to make this a strict cache-only lookup.
    - `mark_accessed_on_return` (default True) bumps access_count and writes
      a retrieval_log row for the returned hits. Set False for read-only
      inspection.
    """
    if not text or not text.strip():
        return []

    domain_tag = domain.value if domain else None
    hits = search(text, limit=limit, domain=domain_tag)

    if not hits and auto_ingest_on_miss:
        attempts = find_and_ingest(
            text, domain=domain,
            prefer_images=prefer_images, keep_images=keep_images,
        )
        if any(a.result is not None for a in attempts):
            # Drop the domain filter: auto-ingest may have landed in a
            # fallback archive with a different tag; widen so we still
            # surface the just-cached article.
            hits = search(text, limit=limit)

    if hits and mark_accessed_on_return:
        mark_accessed([h.article_id for h in hits], query=text, source="cache")

    return hits
