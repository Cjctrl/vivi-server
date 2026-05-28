"""
memory/zim_kb/zim_source.py
libzim wrapper - open ZIM archives and pull individual articles.

libzim is mmap-based: opening an Archive does not load content into memory,
and reading an article streams just that one item. We deliberately do NOT
expose bulk iteration here - conversion / chunking belongs in the next layer.

Run as a script for a small smoke test:
    python -m memory.zim_kb.zim_source
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from libzim.reader import Archive, Entry

from memory.zim_kb.catalog import get_archive as catalog_lookup

logger = logging.getLogger(__name__)


class ZimAccessError(Exception):
    """Raised when a ZIM operation cannot be completed."""


@dataclass(frozen=True)
class ArchiveInfo:
    """Snapshot of an archive's metadata. No content is read to produce this."""
    filename: str
    path: str
    article_count: int
    entry_count: int
    media_count: int
    filesize: int
    uuid: str
    has_main_entry: bool
    has_fulltext_index: bool
    has_title_index: bool


@dataclass(frozen=True)
class ArticleContent:
    """Bytes for one article pulled from a ZIM."""
    title: str                                # ZIM-internal title
    path: str                                 # ZIM-internal path (canonical id in archive)
    mimetype: str
    size: int                                 # uncompressed item size in bytes
    content: bytes
    redirected_from: Optional[str] = None     # original path if we followed a redirect

    @property
    def html(self) -> str:
        return self.content.decode("utf-8", errors="replace")


def open_archive_by_filename(filename: str) -> Archive:
    """Open a catalog-registered ZIM by filename. Raises if unknown or missing."""
    entry = catalog_lookup(filename)
    if entry is None:
        raise ZimAccessError(f"unknown ZIM filename (not in catalog): {filename!r}")
    if not entry.exists():
        raise ZimAccessError(f"ZIM not present on disk: {entry.path}")
    return Archive(entry.path)


def info(arc: Archive, filename: str) -> ArchiveInfo:
    """Snapshot of an archive's metadata. Cheap; no content read."""
    cat = catalog_lookup(filename)
    return ArchiveInfo(
        filename=filename,
        path=str(cat.path) if cat else "",
        article_count=arc.article_count,
        entry_count=arc.entry_count,
        media_count=arc.media_count,
        filesize=arc.filesize,
        uuid=str(arc.uuid),
        has_main_entry=arc.has_main_entry,
        has_fulltext_index=arc.has_fulltext_index,
        has_title_index=arc.has_title_index,
    )


def _resolve_redirects(entry: Entry, *, max_hops: int = 5) -> tuple[Entry, Optional[str]]:
    """Follow a redirect chain. Returns (final_entry, original_path_if_redirected)."""
    original = entry.path if entry.is_redirect else None
    hops = 0
    while entry.is_redirect:
        if hops >= max_hops:
            raise ZimAccessError(f"redirect chain exceeded {max_hops} hops at {entry.path!r}")
        entry = entry.get_redirect_entry()
        hops += 1
    return entry, original


def _entry_to_content(entry: Entry, redirected_from: Optional[str]) -> ArticleContent:
    item = entry.get_item()
    return ArticleContent(
        title=entry.title,
        path=entry.path,
        mimetype=item.mimetype,
        size=item.size,
        content=bytes(item.content),
        redirected_from=redirected_from,
    )


def get_article(arc: Archive, path: str) -> ArticleContent:
    """Pull one article by its ZIM path. Follows redirects. Reads one item."""
    if not arc.has_entry_by_path(path):
        raise ZimAccessError(f"no entry at path: {path!r}")
    entry, original = _resolve_redirects(arc.get_entry_by_path(path))
    return _entry_to_content(entry, original)


def get_article_by_title(arc: Archive, title: str) -> ArticleContent:
    """Pull one article by its ZIM title. Follows redirects."""
    if not arc.has_entry_by_title(title):
        raise ZimAccessError(f"no entry with title: {title!r}")
    entry, original = _resolve_redirects(arc.get_entry_by_title(title))
    return _entry_to_content(entry, original)


def get_main_article(arc: Archive) -> ArticleContent:
    """Pull the archive's main entry, following its redirect if any."""
    if not arc.has_main_entry:
        raise ZimAccessError("archive has no main entry")
    entry, original = _resolve_redirects(arc.main_entry)
    return _entry_to_content(entry, original)


def _main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    test_filename = "devdocs_en_qunit_2026-04.zim"   # smallest registered archive (~3 MB)
    logger.info("smoke test: %s", test_filename)

    arc = open_archive_by_filename(test_filename)
    i = info(arc, test_filename)
    logger.info("info: entries=%d articles=%d media=%d filesize=%.2f MB uuid=%s",
                i.entry_count, i.article_count, i.media_count, i.filesize / 1e6, i.uuid)
    logger.info("indices: fulltext=%s title=%s main=%s",
                i.has_fulltext_index, i.has_title_index, i.has_main_entry)

    main = get_main_article(arc)
    logger.info("main: title=%r path=%r mime=%s size=%d B redirected_from=%r",
                main.title, main.path, main.mimetype, main.size, main.redirected_from)
    if main.mimetype.startswith("text/"):
        preview = " ".join(main.html.split())[:200]
        logger.info("first 200 chars: %s", preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
