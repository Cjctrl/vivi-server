"""
nexus/graph.py
Knowledge graph utilities — edge traversal, backlink index, neighbor queries.

The graph is derived entirely from frontmatter `edges:` lists in .md nodes.
No separate graph database is required; the files *are* the graph.
"""

from __future__ import annotations

import logging
import threading
from collections import defaultdict, deque
from pathlib import Path
from typing import Dict, List, Optional, Set

import yaml

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Frontmatter parsing helpers
# ---------------------------------------------------------------------------

def _parse_frontmatter(text: str) -> tuple[dict, str]:
    """Split a node's raw text into (frontmatter_dict, body).

    Returns ({}, text) if no valid YAML frontmatter block is found.
    """
    if not text.startswith("---"):
        return {}, text
    end = text.find("\n---", 3)
    if end == -1:
        return {}, text
    fm_text = text[3:end].strip()
    body = text[end + 4:].lstrip("\n")
    try:
        fm = yaml.safe_load(fm_text) or {}
    except yaml.YAMLError:
        fm = {}
    return fm, body


def _title_from_path(path: Path, kb_root: Path) -> str:
    """Derive a canonical title string from a node's file path.

    e.g. nexus/knowledge_base/memories/session_abc.md → memories/session_abc
    """
    try:
        rel = path.relative_to(kb_root)
        return str(rel.with_suffix("")).replace("\\", "/")
    except ValueError:
        return path.stem


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------

class KnowledgeGraph:
    """
    In-memory directed graph built by scanning all .md nodes in the KB.

    Attributes
    ----------
    adjacency : dict[title → list[title]]
        Forward edges: nodes each node links *to*.
    backlinks : dict[title → set[title]]
        Reverse index: nodes that link *to* each title.
    """

    def __init__(self) -> None:
        self.adjacency: Dict[str, List[str]] = defaultdict(list)
        self.backlinks: Dict[str, Set[str]] = defaultdict(set)

    # ------------------------------------------------------------------
    # Build / refresh
    # ------------------------------------------------------------------

    def build(self, kb_root: Path) -> None:
        """Scan every .md file in kb_root and (re)build the graph."""
        self.adjacency.clear()
        self.backlinks.clear()

        for md_path in kb_root.rglob("*.md"):
            try:
                raw = md_path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                logger.warning("[graph] cannot read %s: %s", md_path, exc)
                continue

            fm, _ = _parse_frontmatter(raw)
            title = _title_from_path(md_path, kb_root)
            edges: List[str] = fm.get("edges") or []

            for target in edges:
                if isinstance(target, str) and target.strip():
                    t = target.strip()
                    self.adjacency[title].append(t)
                    self.backlinks[t].add(title)

        logger.info(
            "[graph] built: %d nodes, %d edges",
            len(self.adjacency),
            sum(len(v) for v in self.adjacency.values()),
        )

    def add_edge(self, from_title: str, to_title: str) -> None:
        """Register a single directed edge (called when a node is linked live)."""
        if to_title not in self.adjacency[from_title]:
            self.adjacency[from_title].append(to_title)
        self.backlinks[to_title].add(from_title)

    # ------------------------------------------------------------------
    # Query API
    # ------------------------------------------------------------------

    def get_backlinks(self, title: str) -> List[str]:
        """Return all node titles that have an edge pointing to *title*."""
        return sorted(self.backlinks.get(title, set()))

    def get_neighbors(self, title: str, depth: int = 1) -> List[str]:
        """
        BFS outward from *title* up to *depth* hops.

        Returns all reachable nodes (excluding the start node itself),
        ordered by discovery level then alphabetically.
        """
        if depth < 1:
            return []

        visited: Set[str] = {title}
        result: List[str] = []
        queue: deque[tuple[str, int]] = deque([(title, 0)])

        while queue:
            current, level = queue.popleft()
            if level >= depth:
                continue
            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    result.append(neighbor)
                    queue.append((neighbor, level + 1))

        return result

    def get_edges(self, title: str) -> List[str]:
        """Return the direct forward edges for *title*."""
        return list(self.adjacency.get(title, []))


# ---------------------------------------------------------------------------
# Module-level singleton — server and bridge share one graph instance
# ---------------------------------------------------------------------------

_graph: Optional[KnowledgeGraph] = None
_graph_lock = threading.Lock()


def get_graph() -> KnowledgeGraph:
    global _graph
    if _graph is None:
        with _graph_lock:
            if _graph is None:
                _graph = KnowledgeGraph()
    return _graph
