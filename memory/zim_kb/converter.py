"""
memory/zim_kb/converter.py
HTML -> Markdown converter for ZIM articles.

Strips boilerplate (nav, ads, scripts, edit links, images by default) and
converts the remainder to clean Markdown via markdownify. Per-archive
selector refinements can be added by extending _STRIP_SELECTORS.

Run as a script for a smoke test on qunit + one Wikipedia article:
    python -m memory.zim_kb.converter
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from memory.zim_kb.zim_source import ArticleContent

logger = logging.getLogger(__name__)


# Tags removed wholesale.
_STRIP_TAGS: tuple[str, ...] = ("script", "style", "noscript")

# CSS selectors to remove. Covers Wikipedia + DevDocs + generic patterns.
_STRIP_SELECTORS: tuple[str, ...] = (
    # Generic semantic boilerplate
    "nav", "footer", "aside",
    # Generic classes / ids
    ".navigation", ".nav", ".navbar", ".sidebar",
    ".breadcrumb", ".breadcrumbs",
    ".advertisement", ".ad", ".ads",
    ".cookie-banner", ".banner",
    # Wikipedia
    "#mw-navigation", "#mw-page-base", "#mw-head", "#mw-panel",
    ".mw-editsection", ".mw-jump-link", ".mw-indicators",
    ".printfooter", ".catlinks", ".navbox",
    ".refbegin", ".references",
    ".hatnote", ".mw-empty-elt",
    "table.infobox",
    # DevDocs
    "._search", "._sidebar", "._toc", "._lists",
)


@dataclass(frozen=True)
class ConvertedMarkdown:
    title: str
    source_path: str                       # original ZIM path
    markdown: str
    internal_links: tuple[str, ...] = ()   # hrefs that look like in-archive paths
    stripped_counts: dict[str, int] = field(default_factory=dict)


def convert_article(
    article: ArticleContent,
    *,
    keep_images: bool = False,
) -> ConvertedMarkdown:
    """Convert an ArticleContent's HTML to clean Markdown.

    Raises ValueError if the article's mimetype is not text/html.
    """
    if not article.mimetype.startswith("text/html"):
        raise ValueError(f"cannot convert non-HTML article ({article.mimetype!r})")

    soup = BeautifulSoup(article.html, "html.parser")
    stripped: dict[str, int] = {}

    # 1. Strip whole-tag categories.
    for tag_name in _STRIP_TAGS:
        matches = soup.find_all(tag_name)
        if matches:
            stripped[tag_name] = len(matches)
            for el in matches:
                el.decompose()

    # 2. Strip by CSS selector.
    for sel in _STRIP_SELECTORS:
        matches = soup.select(sel)
        if matches:
            stripped[sel] = stripped.get(sel, 0) + len(matches)
            for el in matches:
                el.decompose()

    # 3. Optionally strip images.
    if not keep_images:
        imgs = soup.find_all("img")
        if imgs:
            stripped["img"] = len(imgs)
            for el in imgs:
                el.decompose()

    # 4. Collect internal-looking links (relative hrefs) for the index.
    internal_links: list[str] = []
    seen: set[str] = set()
    for a in soup.find_all("a", href=True):
        href = a["href"].strip()
        if not href or href in seen:
            continue
        if href.startswith(("http://", "https://", "//", "mailto:", "#", "javascript:")):
            continue
        seen.add(href)
        internal_links.append(href)

    # 5. HTML -> Markdown.
    md_text = md(str(soup), heading_style="ATX", bullets="-")

    # 6. Collapse runs of blank lines to at most one.
    out_lines: list[str] = []
    blanks = 0
    for ln in md_text.splitlines():
        if ln.strip() == "":
            blanks += 1
            if blanks <= 1:
                out_lines.append("")
        else:
            blanks = 0
            out_lines.append(ln.rstrip())
    md_text = "\n".join(out_lines).strip() + "\n"

    return ConvertedMarkdown(
        title=article.title,
        source_path=article.path,
        markdown=md_text,
        internal_links=tuple(internal_links),
        stripped_counts=stripped,
    )


def _main() -> int:
    import sys
    # Smoke test only: Windows default console is cp1252 which can't render
    # IPA / extended Unicode. Production cache writes will be UTF-8 explicitly.
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    from memory.zim_kb.zim_source import (
        open_archive_by_filename,
        get_main_article,
        get_article_by_title,
    )

    # ----- Test 1: tiny devdocs article -----------------------------------
    f1 = "devdocs_en_qunit_2026-04.zim"
    logger.info("test 1: %s main page", f1)
    arc1 = open_archive_by_filename(f1)
    art1 = get_main_article(arc1)
    out1 = convert_article(art1)
    logger.info("  %d B HTML -> %d B Markdown  stripped=%s",
                len(art1.content), len(out1.markdown), dict(out1.stripped_counts) or "{}")
    logger.info("  internal links: %d", len(out1.internal_links))
    print("---- BEGIN qunit Markdown (first 600 chars) ----")
    print(out1.markdown[:600])
    print("---- END qunit Markdown ----\n")

    # ----- Test 2: one Wikipedia article ----------------------------------
    f2 = "wikipedia_en_computer_nopic_2026-03.zim"
    logger.info("test 2: %s - try a few titles", f2)
    arc2 = open_archive_by_filename(f2)
    art2 = None
    for title in ("Algorithm", "Quicksort", "Sorting algorithm", "Computer science"):
        try:
            art2 = get_article_by_title(arc2, title)
            logger.info("  picked %r (path=%r)", art2.title, art2.path)
            break
        except Exception:
            continue
    if art2 is None:
        logger.warning("  no test article found; skipping test 2")
        return 0
    out2 = convert_article(art2)
    logger.info("  %d B HTML -> %d B Markdown  stripped=%s",
                len(art2.content), len(out2.markdown), dict(out2.stripped_counts))
    logger.info("  internal links: %d  first 3: %s",
                len(out2.internal_links), list(out2.internal_links[:3]))
    print("---- BEGIN Wikipedia Markdown (first 800 chars) ----")
    print(out2.markdown[:800])
    print("---- END Wikipedia Markdown ----")
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
