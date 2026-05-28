"""
memory/zim_kb/retriever.py
Hybrid retrieval over the ZIM knowledge cache.

Issues queries against the FTS5 indexes (articles_fts on title/tags,
chunks_fts on chunk_text) and fuses results with Reciprocal Rank Fusion.
The RRF skeleton accepts an arbitrary list of rank-dicts, so vector ranks
slot in as a third input later without changing the public API.

search() has NO side effects (per spec: retrieval and usage tracking are
separate). Call mark_accessed() with the ids the caller actually consumed
to bump access_count and append a retrieval_log row.

Run as a script:
    python -m memory.zim_kb.retriever
"""
from __future__ import annotations

import json
import logging
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from memory.zim_kb.db import get_connection

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Hit:
    article_id: int
    title: str
    source_zim: str
    markdown_path: str
    tags: Optional[str]
    rrf_score: float
    fts_article_rank: Optional[int] = None    # 1-indexed; None if not in article-FTS results
    fts_chunk_rank: Optional[int] = None      # best chunk rank for this article (1-indexed)
    vec_chunk_rank: Optional[int] = None      # deferred; always None until embeddings land
    matched_chunk_id: Optional[int] = None
    matched_snippet: Optional[str] = None


def _rrf(rank_lists: list[dict[int, int]], *, k: int = 60) -> dict[int, float]:
    """Reciprocal Rank Fusion.

    Each input dict maps doc_id -> 1-indexed rank (lower = better).
    Returns doc_id -> combined score (higher = better).
    Per the spec's formula: score += 1 / (k + rank).
    """
    scores: dict[int, float] = {}
    for ranks in rank_lists:
        for doc_id, rank in ranks.items():
            scores[doc_id] = scores.get(doc_id, 0.0) + 1.0 / (k + rank)
    return scores


def search(
    query: str,
    *,
    limit: int = 5,
    domain: Optional[str] = None,
    rrf_k: int = 60,
    conn: Optional[sqlite3.Connection] = None,
) -> list[Hit]:
    """Hybrid FTS retrieval. Returns up to `limit` Hit objects ranked by RRF.

    The `query` is passed through to FTS5 verbatim - callers can use FTS5
    syntax (phrase quotes, AND/OR/NOT, prefix*, column filters).
    `domain` filters by articles.tags (set to archive primary_domain at ingest).
    """
    if not query or not query.strip():
        return []

    own = conn is None
    if conn is None:
        conn = get_connection()
    try:
        # ---- Article-level matches (title + tags) -------------------------
        if domain:
            article_sql = (
                "SELECT a.id AS article_id FROM articles_fts fts "
                "JOIN articles a ON a.id = fts.rowid "
                "WHERE articles_fts MATCH ? AND a.tags = ? "
                "ORDER BY fts.rank ASC LIMIT ?"
            )
            article_params: tuple = (query, domain, max(limit * 4, 20))
        else:
            article_sql = (
                "SELECT a.id AS article_id FROM articles_fts fts "
                "JOIN articles a ON a.id = fts.rowid "
                "WHERE articles_fts MATCH ? "
                "ORDER BY fts.rank ASC LIMIT ?"
            )
            article_params = (query, max(limit * 4, 20))

        article_ranks: dict[int, int] = {}
        for i, row in enumerate(conn.execute(article_sql, article_params).fetchall()):
            article_ranks[row["article_id"]] = i + 1

        # ---- Chunk-level matches (body) -----------------------------------
        if domain:
            chunk_sql = (
                "SELECT c.id AS chunk_id, c.article_id, "
                "       snippet(chunks_fts, 0, '[', ']', '...', 12) AS snip "
                "FROM chunks_fts fts "
                "JOIN chunks c ON c.id = fts.rowid "
                "JOIN articles a ON a.id = c.article_id "
                "WHERE chunks_fts MATCH ? AND a.tags = ? "
                "ORDER BY fts.rank ASC LIMIT ?"
            )
            chunk_params: tuple = (query, domain, max(limit * 6, 30))
        else:
            chunk_sql = (
                "SELECT c.id AS chunk_id, c.article_id, "
                "       snippet(chunks_fts, 0, '[', ']', '...', 12) AS snip "
                "FROM chunks_fts fts "
                "JOIN chunks c ON c.id = fts.rowid "
                "WHERE chunks_fts MATCH ? "
                "ORDER BY fts.rank ASC LIMIT ?"
            )
            chunk_params = (query, max(limit * 6, 30))

        # Keep best (= first-seen, = lowest rank) chunk per article.
        per_article_best: dict[int, dict] = {}
        chunk_ranks: dict[int, int] = {}
        for i, row in enumerate(conn.execute(chunk_sql, chunk_params).fetchall()):
            aid = row["article_id"]
            if aid in per_article_best:
                continue
            per_article_best[aid] = {"chunk_id": row["chunk_id"], "snip": row["snip"]}
            chunk_ranks[aid] = i + 1

        # ---- Fuse ---------------------------------------------------------
        fused = _rrf([article_ranks, chunk_ranks], k=rrf_k)
        if not fused:
            return []
        top_ids = sorted(fused, key=fused.__getitem__, reverse=True)[:limit]

        # ---- Hydrate hit metadata in one batch ----------------------------
        placeholders = ",".join("?" * len(top_ids))
        rows = conn.execute(
            f"SELECT id, title, source_zim, markdown_path, tags "
            f"FROM articles WHERE id IN ({placeholders})",
            top_ids,
        ).fetchall()
        meta = {r["id"]: r for r in rows}

        hits: list[Hit] = []
        for aid in top_ids:
            m = meta.get(aid)
            if m is None:
                continue
            ci = per_article_best.get(aid)
            hits.append(Hit(
                article_id=aid,
                title=m["title"],
                source_zim=m["source_zim"],
                markdown_path=m["markdown_path"],
                tags=m["tags"],
                rrf_score=fused[aid],
                fts_article_rank=article_ranks.get(aid),
                fts_chunk_rank=chunk_ranks.get(aid),
                matched_chunk_id=ci["chunk_id"] if ci else None,
                matched_snippet=ci["snip"] if ci else None,
            ))
        return hits
    finally:
        if own:
            conn.close()


def mark_accessed(
    article_ids: list[int],
    *,
    query: Optional[str] = None,
    source: str = "cache",
    conn: Optional[sqlite3.Connection] = None,
) -> None:
    """Bump access_count + last_accessed for the given articles, and append a
    retrieval_log row. Call this after the caller actually uses the hits."""
    if not article_ids:
        return
    own = conn is None
    if conn is None:
        conn = get_connection()
    try:
        ts = datetime.now(timezone.utc).isoformat(timespec="seconds")
        conn.executemany(
            "UPDATE articles SET access_count = access_count + 1, "
            "last_accessed = ? WHERE id = ?",
            [(ts, aid) for aid in article_ids],
        )
        conn.execute(
            "INSERT INTO retrieval_log (query_text, retrieved_from, article_ids, ts) "
            "VALUES (?, ?, ?, ?)",
            (query or "", source, json.dumps(article_ids), ts),
        )
        conn.commit()
    finally:
        if own:
            conn.close()


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    queries = [
        "algorithm",
        "computer science",
        "QUnit",
        "data processing",
        "automated reasoning",
    ]
    last_hits: list[Hit] = []
    for q in queries:
        logger.info("=" * 60)
        logger.info("query: %r", q)
        hits = search(q, limit=5)
        if not hits:
            logger.info("  (no hits)")
            continue
        for i, h in enumerate(hits, 1):
            logger.info(
                "  %d. id=%d rrf=%.4f  art_rank=%s chunk_rank=%s",
                i, h.article_id, h.rrf_score, h.fts_article_rank, h.fts_chunk_rank,
            )
            logger.info("     title=%r source=%s", h.title, h.source_zim)
            if h.matched_snippet:
                logger.info("     snippet: %s", h.matched_snippet[:140])
        last_hits = hits

    # mark_accessed on the last query's hits and verify counts moved.
    if last_hits:
        ids = [h.article_id for h in last_hits]
        mark_accessed(ids, query=queries[-1])
        logger.info("=" * 60)
        logger.info("marked %d articles accessed", len(ids))
        conn = get_connection()
        for aid in ids:
            r = conn.execute(
                "SELECT title, access_count, last_accessed FROM articles WHERE id = ?",
                (aid,),
            ).fetchone()
            logger.info("  id=%d access_count=%d last=%s",
                        aid, r["access_count"], r["last_accessed"])
        log_rows = conn.execute(
            "SELECT query_text, retrieved_from, article_ids, ts "
            "FROM retrieval_log ORDER BY id DESC LIMIT 1"
        ).fetchone()
        logger.info("retrieval_log latest: q=%r from=%s ids=%s ts=%s",
                    log_rows["query_text"], log_rows["retrieved_from"],
                    log_rows["article_ids"], log_rows["ts"])
        conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
