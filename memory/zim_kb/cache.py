"""
memory/zim_kb/cache.py
Markdown cache writer + DB indexer.

Takes a ConvertedMarkdown, writes the .md file under ZIM_KB_MARKDOWN_DIR,
chunks the text, computes SHA-256, and upserts article + chunk records into
nexus_index.sqlite. Idempotent - re-running with identical content is a no-op.
"""
from __future__ import annotations

import hashlib
import logging
import re
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from config.settings import ZIM_KB_MARKDOWN_DIR
from memory.zim_kb.converter import ConvertedMarkdown
from memory.zim_kb.db import get_connection

logger = logging.getLogger(__name__)


# Spec target: ~512 tokens / ~64 token overlap. Char-based heuristic for now
# (rough 4 chars per token); swap for tokenizer-based chunking when the
# embedding model lands.
DEFAULT_CHUNK_CHARS = 2048
DEFAULT_OVERLAP_CHARS = 256
MAX_BOUNDARY_DRIFT = 50          # how far we'll move a chunk edge to land on whitespace


@dataclass(frozen=True)
class IngestResult:
    article_id: int
    markdown_path: Path           # absolute path on disk
    relative_path: str            # path relative to ZIM_KB_MARKDOWN_DIR (stored in DB)
    sha256: str
    chunk_count: int
    was_update: bool              # True if an existing article was overwritten
    was_unchanged: bool           # True if content matched -> no-op


_SLUG_INVALID = re.compile(r"[^\w.\-]+", flags=re.UNICODE)


def slugify(text: str, *, max_chars: int = 120) -> str:
    """Filesystem-safe filename fragment. Keeps unicode word chars, dot, hyphen.
    Collapses runs of underscores. Truncates to max_chars."""
    out = _SLUG_INVALID.sub("_", text).strip("_.")
    out = re.sub(r"_+", "_", out)
    if len(out) > max_chars:
        out = out[:max_chars]
    return out or "untitled"


def compute_sha256(text: str) -> str:
    """SHA-256 hex digest of text encoded as UTF-8."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def chunk_text(
    text: str,
    *,
    chunk_size: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_OVERLAP_CHARS,
) -> list[str]:
    """Sliding-window chunker. Snaps chunk boundaries to whitespace when
    possible. Empty input -> []. Raises if chunk_size <= overlap."""
    if not text or not text.strip():
        return []
    if chunk_size <= overlap:
        raise ValueError("chunk_size must be > overlap")
    chunks: list[str] = []
    n = len(text)
    start = 0
    while start < n:
        end = min(start + chunk_size, n)
        if end < n:
            ws = text.find(" ", end)
            if 0 <= ws - end <= MAX_BOUNDARY_DRIFT:
                end = ws
        piece = text[start:end].strip()
        if piece:
            chunks.append(piece)
        if end >= n:
            break
        next_start = end - overlap
        if next_start <= start:                   # never regress
            next_start = end
        if 0 < next_start < n and text[next_start] != " ":
            ws = text.find(" ", next_start)
            if 0 <= ws - next_start <= MAX_BOUNDARY_DRIFT:
                next_start = ws + 1
        start = next_start
    return chunks


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def cache_converted(
    converted: ConvertedMarkdown,
    *,
    source_zim: str,
    archive_subdir: str,
    archive_domain: str,
    chunk_size: int = DEFAULT_CHUNK_CHARS,
    overlap: int = DEFAULT_OVERLAP_CHARS,
    conn: sqlite3.Connection | None = None,
) -> IngestResult:
    """Write Markdown to the cache and upsert it into the metadata DB.

    Layout on disk:
        <ZIM_KB_MARKDOWN_DIR>/<archive_subdir>/<archive_domain>/<slug>.md

    archive_subdir + archive_domain come from the catalog's Archive
    (Archive.subdir, Archive.primary_domain.value).

    Idempotent: same input -> was_unchanged=True; changed input -> was_update=True
    and old chunks are replaced.
    """
    own_conn = conn is None
    if conn is None:
        conn = get_connection()

    slug = slugify(converted.source_path or converted.title)
    rel_path = f"{archive_subdir}/{archive_domain}/{slug}.md"
    abs_path = Path(ZIM_KB_MARKDOWN_DIR) / rel_path
    abs_path.parent.mkdir(parents=True, exist_ok=True)

    sha = compute_sha256(converted.markdown)

    try:
        existing = conn.execute(
            "SELECT id, sha256, chunk_count FROM articles "
            "WHERE source_zim = ? AND zim_namespace = ?",
            (source_zim, converted.source_path),
        ).fetchone()

        # Fast path - unchanged content with matching on-disk file.
        if existing is not None and existing["sha256"] == sha and abs_path.is_file():
            on_disk = compute_sha256(abs_path.read_text(encoding="utf-8"))
            if on_disk == sha:
                return IngestResult(
                    article_id=existing["id"],
                    markdown_path=abs_path,
                    relative_path=rel_path,
                    sha256=sha,
                    chunk_count=existing["chunk_count"],
                    was_update=False,
                    was_unchanged=True,
                )

        # Write file (overwrite if exists). Always UTF-8.
        abs_path.write_text(converted.markdown, encoding="utf-8")

        chunks = chunk_text(converted.markdown, chunk_size=chunk_size, overlap=overlap)
        chunk_count = len(chunks)
        ts = _now_iso()
        tags = archive_domain

        if existing is None:
            cur = conn.execute(
                """INSERT INTO articles
                   (title, source_zim, zim_namespace, conversion_ts,
                    markdown_path, sha256, embedded, zim_archived,
                    chunk_count, tags)
                   VALUES (?, ?, ?, ?, ?, ?, 0, 0, ?, ?)""",
                (converted.title, source_zim, converted.source_path, ts,
                 rel_path, sha, chunk_count, tags),
            )
            article_id = cur.lastrowid
            was_update = False
        else:
            article_id = existing["id"]
            conn.execute("DELETE FROM chunks WHERE article_id = ?", (article_id,))
            conn.execute(
                """UPDATE articles
                   SET title=?, conversion_ts=?, markdown_path=?, sha256=?,
                       chunk_count=?, tags=?, embedded=0, zim_archived=0
                   WHERE id=?""",
                (converted.title, ts, rel_path, sha, chunk_count, tags, article_id),
            )
            was_update = True

        conn.executemany(
            "INSERT INTO chunks (article_id, chunk_index, chunk_text, sha256) "
            "VALUES (?, ?, ?, ?)",
            [(article_id, i, c, compute_sha256(c)) for i, c in enumerate(chunks)],
        )

        # Verify on-disk content survives the write; only then mark archived.
        on_disk = compute_sha256(abs_path.read_text(encoding="utf-8"))
        if on_disk == sha:
            conn.execute(
                "UPDATE articles SET zim_archived = 1 WHERE id = ?",
                (article_id,),
            )
        else:
            logger.warning("on-disk sha mismatch for %s; zim_archived left at 0", rel_path)

        conn.commit()

        return IngestResult(
            article_id=article_id,
            markdown_path=abs_path,
            relative_path=rel_path,
            sha256=sha,
            chunk_count=chunk_count,
            was_update=was_update,
            was_unchanged=False,
        )
    finally:
        if own_conn:
            conn.close()


def _main() -> int:
    import sys
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    from memory.zim_kb.catalog import get_archive
    from memory.zim_kb.converter import convert_article
    from memory.zim_kb.zim_source import (
        get_article_by_title, get_main_article, open_archive_by_filename,
    )

    # ----- Test 1: qunit main page (tiny) -----
    f1 = "devdocs_en_qunit_2026-04.zim"
    cat1 = get_archive(f1)
    arc1 = open_archive_by_filename(f1)
    art1 = get_main_article(arc1)
    conv1 = convert_article(art1)

    r1 = cache_converted(
        conv1, source_zim=f1,
        archive_subdir=cat1.subdir,
        archive_domain=cat1.primary_domain.value,
    )
    logger.info("qunit ingest: id=%d chunks=%d sha=%s update=%s unchanged=%s",
                r1.article_id, r1.chunk_count, r1.sha256[:12], r1.was_update, r1.was_unchanged)
    logger.info("  file: %s (%d bytes)", r1.markdown_path, r1.markdown_path.stat().st_size)

    # Idempotency check: re-ingest same content.
    r1b = cache_converted(
        conv1, source_zim=f1,
        archive_subdir=cat1.subdir,
        archive_domain=cat1.primary_domain.value,
    )
    logger.info("qunit re-ingest: unchanged=%s update=%s", r1b.was_unchanged, r1b.was_update)
    assert r1b.was_unchanged, "expected no-op on re-ingest"

    # ----- Test 2: Wikipedia 'Algorithm' (chunkable) -----
    f2 = "wikipedia_en_computer_nopic_2026-03.zim"
    cat2 = get_archive(f2)
    arc2 = open_archive_by_filename(f2)
    art2 = None
    for title in ("Algorithm", "Quicksort", "Sorting algorithm"):
        try:
            art2 = get_article_by_title(arc2, title)
            break
        except Exception:
            continue
    if art2 is None:
        logger.warning("no Wikipedia test article found; skipping test 2")
        return 0
    conv2 = convert_article(art2)
    r2 = cache_converted(
        conv2, source_zim=f2,
        archive_subdir=cat2.subdir,
        archive_domain=cat2.primary_domain.value,
    )
    logger.info("wiki ingest: id=%d chunks=%d sha=%s update=%s unchanged=%s",
                r2.article_id, r2.chunk_count, r2.sha256[:12], r2.was_update, r2.was_unchanged)
    logger.info("  file: %s (%d bytes)", r2.markdown_path, r2.markdown_path.stat().st_size)

    # ----- Verify FTS5 + chunks_fts see the new content -----
    conn = get_connection()

    art_hits = conn.execute(
        "SELECT a.id, a.title, a.source_zim, a.chunk_count "
        "FROM articles_fts f JOIN articles a ON a.id = f.rowid "
        "WHERE articles_fts MATCH ? LIMIT 5",
        ("algorithm",),
    ).fetchall()
    logger.info("articles_fts MATCH 'algorithm' -> %d hits", len(art_hits))
    for m in art_hits:
        logger.info("  id=%d title=%r source=%s chunks=%d",
                    m["id"], m["title"], m["source_zim"], m["chunk_count"])

    chunk_hits = conn.execute(
        "SELECT c.id, c.article_id, c.chunk_index, "
        "       snippet(chunks_fts, 0, '[', ']', '...', 10) AS snip "
        "FROM chunks_fts f JOIN chunks c ON c.id = f.rowid "
        "WHERE chunks_fts MATCH ? LIMIT 3",
        ("algorithm",),
    ).fetchall()
    logger.info("chunks_fts MATCH 'algorithm' -> %d hits (showing 3)", len(chunk_hits))
    for h in chunk_hits:
        logger.info("  chunk %d/%d: %s", h["chunk_index"], h["article_id"], h["snip"])

    conn.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
