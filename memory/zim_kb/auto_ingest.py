"""
memory/zim_kb/auto_ingest.py
Auto-fetch articles from ZIM on cache miss.

When retriever.search() returns no hits, this module finds the best
matching article in the candidate ZIM(s) (via catalog.route_query()) and
runs the full fetch -> convert -> cache pipeline so a subsequent search
will find the new content via FTS5.

Match strategy per archive:
  1. exact title (with case variants) - cheapest
  2. SuggestionSearcher           - title-based fuzzy
  3. Searcher (fulltext)          - if the archive has a fulltext index

Run as a script for a smoke test:
    python -m memory.zim_kb.auto_ingest
"""
from __future__ import annotations

import logging
import sqlite3
from dataclasses import dataclass
from typing import Optional

from libzim.reader import Archive as LibzimArchive
from libzim.reader import Entry
from libzim.search import Query, Searcher
from libzim.suggestion import SuggestionSearcher

from memory.zim_kb.cache import IngestResult, cache_converted
from memory.zim_kb.catalog import (
    Archive as CatalogArchive,
    Domain,
    get_archive,
    route_query,
)
from memory.zim_kb.converter import convert_article
from memory.zim_kb.zim_source import (
    ZimAccessError,
    get_article,
    open_archive_by_filename,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class IngestionAttempt:
    archive_filename: str
    match_method: str                       # exact_title | title_case | suggestion | fulltext | not_found | error
    matched_path: Optional[str] = None
    matched_title: Optional[str] = None
    result: Optional[IngestResult] = None
    error: Optional[str] = None


def _candidate_titles(query: str) -> list[str]:
    """Reasonable case variants to try as exact titles, deduplicated."""
    seen: list[str] = []
    for c in (query.strip(), query.title(), query.capitalize()):
        if c and c not in seen:
            seen.append(c)
    return seen


def _ingest_entry(
    arc: LibzimArchive,
    entry: Entry,
    cat: CatalogArchive,
    archive_filename: str,
    *,
    method: str,
    conn: Optional[sqlite3.Connection],
    keep_images: bool,
) -> IngestionAttempt:
    """Pull entry's content, convert, cache. Redirects handled by get_article."""
    try:
        content = get_article(arc, entry.path)
    except ZimAccessError as e:
        return IngestionAttempt(
            archive_filename=archive_filename, match_method="error",
            matched_path=entry.path, matched_title=entry.title, error=str(e),
        )
    if not content.mimetype.startswith("text/html"):
        return IngestionAttempt(
            archive_filename=archive_filename, match_method="not_found",
            matched_path=content.path, matched_title=content.title,
            error=f"non-HTML mimetype {content.mimetype!r}",
        )
    converted = convert_article(content, keep_images=keep_images)
    result = cache_converted(
        converted,
        source_zim=archive_filename,
        archive_subdir=cat.subdir,
        archive_domain=cat.primary_domain.value,
        conn=conn,
    )
    return IngestionAttempt(
        archive_filename=archive_filename, match_method=method,
        matched_path=content.path, matched_title=content.title, result=result,
    )


def find_and_ingest_in(
    query: str,
    archive_filename: str,
    *,
    conn: Optional[sqlite3.Connection] = None,
    keep_images: bool = False,
    use_fulltext_fallback: bool = True,
    max_candidates: int = 5,
) -> IngestionAttempt:
    """Try strategy chain in ONE archive. Returns first successful ingest,
    or an IngestionAttempt with match_method='not_found' / 'error'."""
    cat = get_archive(archive_filename)
    if cat is None:
        return IngestionAttempt(
            archive_filename=archive_filename, match_method="error",
            error=f"unknown archive: {archive_filename!r}",
        )
    try:
        arc = open_archive_by_filename(archive_filename)
    except ZimAccessError as e:
        return IngestionAttempt(
            archive_filename=archive_filename, match_method="error", error=str(e),
        )

    # 1) Exact title (with case variants).
    if arc.has_title_index:
        for cand in _candidate_titles(query):
            try:
                if arc.has_entry_by_title(cand):
                    entry = arc.get_entry_by_title(cand)
                    method = "exact_title" if cand == query.strip() else "title_case"
                    return _ingest_entry(arc, entry, cat, archive_filename,
                                         method=method, conn=conn,
                                         keep_images=keep_images)
            except Exception as e:
                logger.debug("title lookup failed for %r in %s: %r",
                             cand, archive_filename, e)

    # 2) Suggestion (title-based fuzzy).
    if arc.has_title_index:
        try:
            sug = SuggestionSearcher(arc).suggest(query)
            for path in sug.getResults(0, max_candidates):
                if arc.has_entry_by_path(path):
                    entry = arc.get_entry_by_path(path)
                    return _ingest_entry(arc, entry, cat, archive_filename,
                                         method="suggestion", conn=conn,
                                         keep_images=keep_images)
        except Exception as e:
            logger.debug("suggestion failed for %s: %r", archive_filename, e)

    # 3) Fulltext (if the archive has the index).
    if use_fulltext_fallback and arc.has_fulltext_index:
        try:
            search = Searcher(arc).search(Query().set_query(query))
            for path in search.getResults(0, max_candidates):
                if arc.has_entry_by_path(path):
                    entry = arc.get_entry_by_path(path)
                    return _ingest_entry(arc, entry, cat, archive_filename,
                                         method="fulltext", conn=conn,
                                         keep_images=keep_images)
        except Exception as e:
            logger.debug("fulltext search failed for %s: %r", archive_filename, e)

    return IngestionAttempt(archive_filename=archive_filename, match_method="not_found")


def find_and_ingest(
    query: str,
    *,
    domain: Optional[Domain] = None,
    prefer_images: bool = False,
    keep_images: bool = False,
    max_archives: int = 3,
    stop_on_first: bool = True,
    conn: Optional[sqlite3.Connection] = None,
) -> list[IngestionAttempt]:
    """Walk catalog.route_query(domain) and try each archive in turn.

    Stops after the first successful ingest (default) or after exhausting
    `max_archives`. If `domain` is None, defaults to WIKIPEDIA_GENERAL as
    a broad fallback.

    Returns the chronological list of attempts (most recent last).
    """
    target = domain or Domain.WIKIPEDIA_GENERAL
    archives = route_query(target, prefer_images=prefer_images)[:max_archives]
    attempts: list[IngestionAttempt] = []
    for arc_entry in archives:
        attempt = find_and_ingest_in(
            query, arc_entry.filename,
            conn=conn, keep_images=keep_images,
        )
        attempts.append(attempt)
        if stop_on_first and attempt.result is not None:
            break
    return attempts


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from memory.zim_kb.retriever import search

    q = "Quicksort"
    dom = Domain.COMPUTER_SCIENCE
    logger.info("query: %r  domain: %s", q, dom.value)

    pre = search(q)
    logger.info("pre-ingest hits: %d", len(pre))
    for h in pre:
        logger.info("  pre  %r (id=%d)", h.title, h.article_id)

    attempts = find_and_ingest(q, domain=dom, max_archives=3)
    logger.info("ingest attempts: %d", len(attempts))
    for a in attempts:
        if a.result:
            logger.info("  %s [%s]: matched %r -> id=%d chunks=%d (update=%s unchanged=%s)",
                        a.archive_filename, a.match_method, a.matched_title,
                        a.result.article_id, a.result.chunk_count,
                        a.result.was_update, a.result.was_unchanged)
        elif a.error:
            logger.info("  %s [%s]: error %s", a.archive_filename, a.match_method, a.error)
        else:
            logger.info("  %s [%s]: no match", a.archive_filename, a.match_method)

    post = search(q)
    logger.info("post-ingest hits: %d", len(post))
    for h in post[:3]:
        logger.info("  post %r (id=%d, rrf=%.4f, art_rank=%s, chunk_rank=%s)",
                    h.title, h.article_id, h.rrf_score,
                    h.fts_article_rank, h.fts_chunk_rank)
        if h.matched_snippet:
            logger.info("    snippet: %s", h.matched_snippet[:140])
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
