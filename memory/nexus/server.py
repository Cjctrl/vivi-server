"""
nexus/server.py
NEXUS HTTP gateway — binds NEXUS_HOST:NEXUS_PORT (default 127.0.0.1:7200).

Every agent interaction with the knowledge base goes through these routes.
No agent may call Qdrant directly; this server is the sole gateway.

Start:
    python -m memory.nexus.server
    # or from main_vivi.py startup sequence

Routes (all under /api/nodes/):
    GET  /api/nodes/search                     ?q=...&limit=5&semantic=true
    GET  /api/nodes/{title}                    fetch a node by title/path
    GET  /api/nodes/{title}/backlinks          nodes linking → title
    GET  /api/nodes/{title}/neighbors          ?depth=1
    GET  /api/tags/{tag}                       all nodes with a given tag
    POST /api/nodes                            create a new node
    POST /api/nodes/{title}/append             append text to a node
    POST /api/nodes/{title}/link               add directed edge
    PATCH /api/nodes/{title}/frontmatter       patch YAML fields
    POST /api/nodes/reembed                    re-embed a single node (file watcher)
    DELETE /api/nodes/{title}                  delete a node
    GET  /health                               liveness probe
"""

from __future__ import annotations

import asyncio
import hmac
import json
import logging
import os
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from aiohttp import web


def _atomic_write_text(path: Path, content: str, encoding: str = "utf-8") -> None:
    """Write text atomically: write to a sibling temp file, then os.replace into place.

    Guarantees: either the old file persists unchanged, or the new content is fully
    written and visible. No half-written state is observable to readers.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding=encoding) as fh:
            fh.write(content)
        os.replace(tmp, path)
    except Exception:
        try:
            os.remove(tmp)
        except OSError:
            pass
        raise

from config.settings import (
    MEMORY_DB_PATH,
    NEXUS_HOST,
    NEXUS_KB_PATH,
    NEXUS_PORT,
    NEXUS_REQUIRE_READ_AUTH,
    NEXUS_SECRET,
    VECTOR_DIMENSION,
)
from core.vector_store import VectorStore, get_embedding_service, get_vector_store
from memory.nexus.graph import KnowledgeGraph, get_graph, _parse_frontmatter, _title_from_path

logger = logging.getLogger(__name__)

NEXUS_COLLECTION = "nexus_kb"
_UUID_NS = uuid.NAMESPACE_DNS


def _spawn_tracked(app: web.Application, coro) -> asyncio.Task:
    """Schedule a fire-and-forget coroutine with a strong reference held in app['_bg_tasks'].

    Python 3.11+ may GC tasks that have no strong reference; this guarantees the
    embedding task survives until completion regardless.
    """
    task = asyncio.create_task(coro)
    app["_bg_tasks"].add(task)
    task.add_done_callback(app["_bg_tasks"].discard)
    return task

# ---------------------------------------------------------------------------
# Agent color palette — one neon color per registered agent
# ---------------------------------------------------------------------------
AGENT_COLORS: Dict[str, str] = {
    "web_search":           "#FF6B6B",
    "vault_search":         "#4ECDC4",
    "semantic_search":      "#45B7D1",
    "local_file_search":    "#96CEB4",
    "graph_traversal":      "#9B59B6",
    "tool_discovery":       "#E67E22",
    "coding_agent":         "#2ECC71",
    "reasoning_agent":      "#F39C12",
    "math_agent":           "#E74C3C",
    "reflection_agent":     "#8E44AD",
    "visual_context_agent": "#16A085",
    "app_launcher":         "#27AE60",
    "recap_agent":          "#2980B9",
    "capability_discovery": "#C0392B",
}

# ---------------------------------------------------------------------------
# Interaction store — tracks which agents read/wrote which nodes.
# shape: { node_title: { agent_name: { "reads": N, "writes": N } } }
# ---------------------------------------------------------------------------
_INTERACTIONS_PATH = Path(__file__).parent / "agent_interactions.json"
_interactions: Dict[str, Dict[str, Dict[str, int]]] = {}


def _load_interactions() -> None:
    global _interactions
    if _INTERACTIONS_PATH.exists():
        try:
            _interactions = json.loads(_INTERACTIONS_PATH.read_text("utf-8"))
        except Exception:
            logger.warning("interactions_load_failed", exc_info=True)
            _interactions = {}


def _save_interactions() -> None:
    try:
        _atomic_write_text(_INTERACTIONS_PATH, json.dumps(_interactions, indent=2))
    except Exception as exc:
        logger.warning("[nexus/interactions] save failed: %s", exc)


def _record(title: str, agent: str, kind: str) -> None:
    """Record a read or write interaction (kind = 'read' | 'write')."""
    if not agent or agent == "unknown":
        return
    node_data = _interactions.setdefault(title, {})
    agent_data = node_data.setdefault(agent, {"reads": 0, "writes": 0})
    agent_data[f"{kind}s"] += 1
    if kind == "write":
        _save_interactions()


# ===========================================================================
# Node helpers
# ===========================================================================

def _title_to_path(title: str, kb_root: Path) -> Path:
    """Convert a title like 'memories/session_abc' to an absolute .md path.

    Hardened against path traversal: rather than scrubbing "..", we resolve the
    final path and require it to stay inside kb_root. String scrubbing is
    insufficient — `.replace("..", "")` turns "../../etc/passwd" into
    "//etc/passwd", and absolute paths, drive letters, and symlinks slip past it
    entirely. resolve() + is_relative_to() catches all of those.
    """
    candidate = (kb_root / title.strip("/")).with_suffix(".md")
    resolved = candidate.resolve()
    if not resolved.is_relative_to(kb_root.resolve()):
        raise web.HTTPForbidden(reason="Path outside KB root")
    return resolved


def _path_to_title(path: Path, kb_root: Path) -> str:
    return _title_from_path(path, kb_root)


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_node(title: str, fm: dict, body: str) -> dict:
    """Serialize a node to the wire format returned by the API."""
    return {
        "title": title,
        "type": fm.get("type", "note"),
        "tags": fm.get("tags") or [],
        "edges": fm.get("edges") or [],
        "created": fm.get("created", ""),
        "updated": fm.get("updated", ""),
        "body": body,
        "frontmatter": fm,
    }


def _build_frontmatter(fm: dict) -> str:
    """Serialise a frontmatter dict to the YAML block (with --- delimiters)."""
    return "---\n" + yaml.dump(fm, allow_unicode=True, default_flow_style=False) + "---\n"


def _write_node_file(path: Path, fm: dict, body: str) -> None:
    _atomic_write_text(path, _build_frontmatter(fm) + "\n" + body.lstrip("\n"))


def _read_node_file(path: Path, kb_root: Path) -> Optional[dict]:
    """Read a .md file and return the wire-format dict, or None if missing."""
    if not path.exists():
        return None
    try:
        raw = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return None
    fm, body = _parse_frontmatter(raw)
    title = _path_to_title(path, kb_root)
    return _render_node(title, fm, body)


def _find_nodes_by_tag(tag: str, kb_root: Path) -> List[dict]:
    """Scan all .md files and return nodes tagged with *tag*."""
    results = []
    tag_lower = tag.lower().lstrip("#")
    for md_path in sorted(kb_root.rglob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        fm, body = _parse_frontmatter(raw)
        node_tags = [str(t).lower().lstrip("#") for t in (fm.get("tags") or [])]
        if tag_lower in node_tags:
            results.append(_render_node(_path_to_title(md_path, kb_root), fm, body))
    return results


def _build_node_meta(kb_root: Path) -> Dict[str, dict]:
    """Scan all vault .md files and return a lightweight title→{type,tags} index."""
    meta: Dict[str, dict] = {}
    for md_path in sorted(kb_root.rglob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8", errors="ignore")
            fm, _ = _parse_frontmatter(raw)
            t = _path_to_title(md_path, kb_root)
            meta[t] = {"type": fm.get("type", "note"), "tags": fm.get("tags") or []}
        except Exception:
            pass
    return meta


def _fulltext_search(query: str, kb_root: Path, limit: int) -> List[dict]:
    """Simple case-insensitive substring search across all node bodies."""
    results = []
    q = query.lower()
    for md_path in sorted(kb_root.rglob("*.md")):
        try:
            raw = md_path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        if q in raw.lower():
            fm, body = _parse_frontmatter(raw)
            results.append(_render_node(_path_to_title(md_path, kb_root), fm, body))
        if len(results) >= limit:
            break
    return results


# ===========================================================================
# Embedding / indexing helpers
# ===========================================================================

_CHUNK_MAX = 500
_CHUNK_OVERLAP = 100


def _chunk_body(body: str) -> List[str]:
    """Split a body into overlapping chunks for embedding."""
    if len(body) <= _CHUNK_MAX:
        return [body] if body.strip() else []
    chunks = []
    start = 0
    while start < len(body):
        end = min(start + _CHUNK_MAX, len(body))
        chunks.append(body[start:end])
        if end == len(body):
            break
        start = end - _CHUNK_OVERLAP
    return chunks


async def _embed_node(
    title: str,
    body: str,
    store: VectorStore,
    embedder,
    loop: asyncio.AbstractEventLoop,
) -> None:
    """Embed all chunks of a node and upsert into Qdrant (run in executor)."""
    from qdrant_client.http.models import PointStruct

    chunks = _chunk_body(body)
    if not chunks:
        return

    points = []
    for idx, chunk in enumerate(chunks):
        try:
            vector = await loop.run_in_executor(None, embedder.embed, chunk)
        except Exception as exc:
            logger.warning("[nexus/embed] chunk %d of '%s' failed: %s", idx, title, exc)
            continue
        point_id = str(uuid.uuid5(_UUID_NS, f"{title}:{idx}:{chunk[:50]}"))
        points.append(
            PointStruct(
                id=point_id,
                vector=vector,
                payload={"title": title, "chunk_idx": idx, "text": chunk},
            )
        )

    if points:
        await loop.run_in_executor(
            None, store.upsert_points, NEXUS_COLLECTION, points
        )
        logger.debug("[nexus/embed] indexed %d chunks for '%s'", len(points), title)


async def _delete_node_vectors(
    title: str, store: VectorStore, loop: asyncio.AbstractEventLoop
) -> None:
    """Remove all Qdrant points for a given node title."""
    try:
        from qdrant_client.models import Filter, FieldCondition, MatchValue
        await loop.run_in_executor(
            None,
            lambda: store.client.delete(
                collection_name=NEXUS_COLLECTION,
                points_selector=Filter(
                    must=[FieldCondition(key="title", match=MatchValue(value=title))]
                ),
            ),
        )
    except Exception as exc:
        logger.warning("[nexus/embed] vector delete failed for '%s': %s", title, exc)


# ===========================================================================
# Authentication — gate mutating endpoints behind a shared secret
# ===========================================================================

# Methods that mutate the knowledge base. GET routes stay open (read-only,
# localhost-bound); everything that writes must present the secret. Mirrors the
# overlay WS HMAC gate, which similarly lets reads/metrics flow but requires the
# shared secret before honouring destructive commands.
_MUTATING_METHODS: frozenset[str] = frozenset({"POST", "PATCH", "DELETE"})


def _extract_token(request: web.Request) -> str:
    """Pull the caller's token from either header form.

    Accepts `Authorization: Bearer <token>` or `X-Nexus-Token: <token>`.
    Returns "" when neither is present.
    """
    token = request.headers.get("X-Nexus-Token", "").strip()
    if token:
        return token
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):].strip()
    return ""


def _token_ok(request: web.Request) -> bool:
    """True when the request carries the valid NEXUS shared secret."""
    provided = _extract_token(request)
    # compare_digest is timing-safe; both operands must be non-empty.
    return bool(provided) and hmac.compare_digest(provided, NEXUS_SECRET)


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """Gate mutating requests behind the NEXUS shared secret.

    Reads stay open by default (localhost-bound). Set NEXUS_REQUIRE_READ_AUTH to
    also require the token on data reads (GET /api/*); /health and the static UI
    shell stay open regardless. The agent bridge already sends the token on every
    request, so enabling read-auth only affects unauthenticated callers such as a
    browser hitting the graph UI.
    """
    is_mutation = request.method in _MUTATING_METHODS
    is_gated_read = (
        NEXUS_REQUIRE_READ_AUTH
        and request.method == "GET"
        and request.path.startswith("/api/")
    )
    if (is_mutation or is_gated_read) and not _token_ok(request):
        logger.warning(
            "[nexus/auth] rejected unauthenticated %s %s",
            request.method, request.path,
        )
        return web.json_response(
            {"error": "Unauthorized — valid Bearer token or X-Nexus-Token header required"},
            status=401,
        )
    return await handler(request)


# ===========================================================================
# Route handlers
# ===========================================================================

async def handle_health(request: web.Request) -> web.Response:
    return web.json_response({"status": "ok", "service": "nexus", "port": NEXUS_PORT})


# ── Search ─────────────────────────────────────────────────────────────────

async def handle_search(request: web.Request) -> web.Response:
    """
    GET /api/nodes/search?q=...&limit=5&semantic=true&fulltext=true

    Merges semantic (Qdrant) and full-text results, deduped by title.
    """
    q = request.rel_url.query.get("q", "").strip()
    if not q:
        return web.json_response({"error": "q is required"}, status=400)

    limit = int(request.rel_url.query.get("limit", 5))
    do_semantic = request.rel_url.query.get("semantic", "true").lower() != "false"
    do_fulltext = request.rel_url.query.get("fulltext", "true").lower() != "false"

    store: VectorStore = request.app["store"]
    embedder = request.app["embedder"]
    kb_root: Path = request.app["kb_root"]
    loop = asyncio.get_running_loop()

    seen_titles: set = set()
    results: List[dict] = []

    # Semantic search via Qdrant
    if do_semantic:
        try:
            vector = await loop.run_in_executor(None, embedder.embed, q)
            hits = await loop.run_in_executor(
                None,
                lambda: store.search(NEXUS_COLLECTION, vector, limit=limit * 2, score_threshold=0.3),
            )
            for pt in hits:
                title = (pt.payload or {}).get("title", "")
                if not title or title in seen_titles:
                    continue
                node = _read_node_file(_title_to_path(title, kb_root), kb_root)
                if node:
                    node["_score"] = float(pt.score)
                    node["_match"] = "semantic"
                    results.append(node)
                    seen_titles.add(title)
                if len(results) >= limit:
                    break
        except Exception as exc:
            logger.warning("[nexus/search] semantic search failed: %s", exc)

    # Full-text fallback / supplement
    if do_fulltext and len(results) < limit:
        ft_hits = await loop.run_in_executor(
            None, _fulltext_search, q, kb_root, limit - len(results)
        )
        for node in ft_hits:
            if node["title"] not in seen_titles:
                node["_score"] = 0.5
                node["_match"] = "fulltext"
                results.append(node)
                seen_titles.add(node["title"])

    agent = request.headers.get("X-Agent-Name", "unknown")
    for node in results:
        _record(node["title"], agent, "read")

    return web.json_response({"query": q, "count": len(results), "results": results})


# ── Get node ────────────────────────────────────────────────────────────────

async def handle_get_node(request: web.Request) -> web.Response:
    """GET /api/nodes/{title}"""
    title = request.match_info["title"]
    kb_root: Path = request.app["kb_root"]
    node = _read_node_file(_title_to_path(title, kb_root), kb_root)
    if node is None:
        return web.json_response({"error": f"Node '{title}' not found"}, status=404)
    _record(title, request.headers.get("X-Agent-Name", "unknown"), "read")
    return web.json_response(node)


# ── Backlinks ────────────────────────────────────────────────────────────────

async def handle_get_backlinks(request: web.Request) -> web.Response:
    """GET /api/nodes/{title}/backlinks"""
    title = request.match_info["title"]
    graph: KnowledgeGraph = request.app["graph"]
    backlinks = graph.get_backlinks(title)
    _record(title, request.headers.get("X-Agent-Name", "unknown"), "read")
    return web.json_response({"title": title, "backlinks": backlinks, "count": len(backlinks)})


# ── Neighbors ────────────────────────────────────────────────────────────────

async def handle_get_neighbors(request: web.Request) -> web.Response:
    """GET /api/nodes/{title}/neighbors?depth=1"""
    title = request.match_info["title"]
    depth = int(request.rel_url.query.get("depth", 1))
    graph: KnowledgeGraph = request.app["graph"]
    neighbors = graph.get_neighbors(title, depth=depth)
    _record(title, request.headers.get("X-Agent-Name", "unknown"), "read")
    return web.json_response({"title": title, "depth": depth, "neighbors": neighbors})


# ── Get by tag ────────────────────────────────────────────────────────────────

async def handle_get_by_tag(request: web.Request) -> web.Response:
    """GET /api/tags/{tag}"""
    tag = request.match_info["tag"]
    kb_root: Path = request.app["kb_root"]
    loop = asyncio.get_running_loop()
    nodes = await loop.run_in_executor(None, _find_nodes_by_tag, tag, kb_root)
    agent = request.headers.get("X-Agent-Name", "unknown")
    for node in nodes:
        _record(node["title"], agent, "read")
    return web.json_response({"tag": tag, "count": len(nodes), "nodes": nodes})


# ── Create node ────────────────────────────────────────────────────────────────

async def handle_create_node(request: web.Request) -> web.Response:
    """
    POST /api/nodes
    Body: {title, body, tags?, type?, edges?}
    """
    try:
        data: dict = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    title: str = (data.get("title") or "").strip()
    if not title:
        return web.json_response({"error": "title is required"}, status=400)

    kb_root: Path = request.app["kb_root"]
    node_path = _title_to_path(title, kb_root)

    now = _now_iso()
    fm: dict = {
        "title": title,
        "created": now,
        "updated": now,
        "tags": data.get("tags") or [],
        "type": data.get("type") or "note",
        "edges": data.get("edges") or [],
    }
    body: str = data.get("body") or ""

    _write_node_file(node_path, fm, body)

    # Update graph edges
    graph: KnowledgeGraph = request.app["graph"]
    for target in fm["edges"]:
        graph.add_edge(title, target)

    # Re-embed asynchronously
    store: VectorStore = request.app["store"]
    embedder = request.app["embedder"]
    loop = asyncio.get_running_loop()
    _spawn_tracked(request.app, _embed_node(title, body, store, embedder, loop))

    _record(title, request.headers.get("X-Agent-Name", "unknown"), "write")
    # Keep node_meta cache in sync
    node_meta: dict = request.app.get("node_meta", {})
    node_meta[title] = {"type": fm["type"], "tags": fm["tags"]}

    return web.json_response(_render_node(title, fm, body), status=201)


# ── Append ────────────────────────────────────────────────────────────────────

async def handle_append(request: web.Request) -> web.Response:
    """
    POST /api/nodes/{title}/append
    Body: {text}
    """
    title = request.match_info["title"]
    try:
        data: dict = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    text: str = data.get("text") or ""
    if not text:
        return web.json_response({"error": "text is required"}, status=400)

    kb_root: Path = request.app["kb_root"]
    node_path = _title_to_path(title, kb_root)

    if not node_path.exists():
        return web.json_response({"error": f"Node '{title}' not found"}, status=404)

    raw = node_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = _parse_frontmatter(raw)

    body = body.rstrip("\n") + "\n\n" + text.strip()
    fm["updated"] = _now_iso()
    _write_node_file(node_path, fm, body)

    # Re-embed new content
    store: VectorStore = request.app["store"]
    embedder = request.app["embedder"]
    loop = asyncio.get_running_loop()
    _spawn_tracked(request.app, _embed_node(title, body, store, embedder, loop))

    _record(title, request.headers.get("X-Agent-Name", "unknown"), "write")

    return web.json_response(_render_node(title, fm, body))


# ── Update frontmatter ────────────────────────────────────────────────────────

async def handle_update_frontmatter(request: web.Request) -> web.Response:
    """
    PATCH /api/nodes/{title}/frontmatter
    Body: {field: value, ...}  (merges into existing frontmatter)
    """
    title = request.match_info["title"]
    try:
        fields: dict = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    kb_root: Path = request.app["kb_root"]
    node_path = _title_to_path(title, kb_root)

    if not node_path.exists():
        return web.json_response({"error": f"Node '{title}' not found"}, status=404)

    raw = node_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = _parse_frontmatter(raw)

    fm.update(fields)
    fm["updated"] = _now_iso()
    _write_node_file(node_path, fm, body)

    # Sync new edges into graph
    graph: KnowledgeGraph = request.app["graph"]
    for target in fm.get("edges") or []:
        graph.add_edge(title, target)

    _record(title, request.headers.get("X-Agent-Name", "unknown"), "write")

    return web.json_response(_render_node(title, fm, body))


# ── Link ──────────────────────────────────────────────────────────────────────

async def handle_link(request: web.Request) -> web.Response:
    """
    POST /api/nodes/{title}/link
    Body: {to: "target/title"}
    """
    from_title = request.match_info["title"]
    try:
        data: dict = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    to_title: str = (data.get("to") or "").strip()
    if not to_title:
        return web.json_response({"error": "to is required"}, status=400)

    kb_root: Path = request.app["kb_root"]
    node_path = _title_to_path(from_title, kb_root)

    if not node_path.exists():
        return web.json_response({"error": f"Node '{from_title}' not found"}, status=404)

    raw = node_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = _parse_frontmatter(raw)

    edges: List[str] = fm.get("edges") or []
    if to_title not in edges:
        edges.append(to_title)
    fm["edges"] = edges
    fm["updated"] = _now_iso()
    _write_node_file(node_path, fm, body)

    graph: KnowledgeGraph = request.app["graph"]
    graph.add_edge(from_title, to_title)

    _record(from_title, request.headers.get("X-Agent-Name", "unknown"), "write")

    return web.json_response({"from": from_title, "to": to_title, "edges": edges})


# ── Re-embed (called by file_watcher.js) ─────────────────────────────────────

async def handle_reembed(request: web.Request) -> web.Response:
    """
    POST /api/nodes/reembed
    Body: {path: "absolute/or/relative path to .md file"}

    Called by file_watcher.js when a node file changes on disk.
    Deletes old vectors and re-indexes the new content.
    """
    try:
        data: dict = await request.json()
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)

    file_path_str: str = (data.get("path") or "").strip()
    if not file_path_str:
        return web.json_response({"error": "path is required"}, status=400)

    kb_root: Path = request.app["kb_root"]
    file_path = Path(file_path_str)

    if not file_path.is_absolute():
        file_path = kb_root / file_path

    if not file_path.exists():
        return web.json_response({"error": f"File not found: {file_path}"}, status=404)

    title = _path_to_title(file_path, kb_root)
    raw = file_path.read_text(encoding="utf-8", errors="ignore")
    fm, body = _parse_frontmatter(raw)

    store: VectorStore = request.app["store"]
    embedder = request.app["embedder"]
    loop = asyncio.get_running_loop()

    # Remove stale vectors, re-embed fresh content
    await _delete_node_vectors(title, store, loop)
    await _embed_node(title, body, store, embedder, loop)

    # Refresh graph edges from updated frontmatter
    graph: KnowledgeGraph = request.app["graph"]
    for target in fm.get("edges") or []:
        graph.add_edge(title, target)

    return web.json_response({"status": "reembedded", "title": title})


# ── Delete node ───────────────────────────────────────────────────────────────

async def handle_delete_node(request: web.Request) -> web.Response:
    """DELETE /api/nodes/{title}"""
    title = request.match_info["title"]
    kb_root: Path = request.app["kb_root"]
    node_path = _title_to_path(title, kb_root)

    if not node_path.exists():
        return web.json_response({"error": f"Node '{title}' not found"}, status=404)

    node_path.unlink()

    store: VectorStore = request.app["store"]
    loop = asyncio.get_running_loop()
    await _delete_node_vectors(title, store, loop)

    _record(title, request.headers.get("X-Agent-Name", "unknown"), "write")
    # Remove from node_meta cache
    request.app.get("node_meta", {}).pop(title, None)

    return web.json_response({"status": "deleted", "title": title})


# ── Graph endpoint ────────────────────────────────────────────────────────────

async def handle_get_graph(request: web.Request) -> web.Response:
    """
    GET /api/graph
    Returns D3-compatible nodes + links. The per-node agent-interaction map is
    included only for authenticated callers (it reveals which agents touched
    which nodes); unauthenticated callers get an empty map.
    """
    graph: KnowledgeGraph = request.app["graph"]
    node_meta: Dict[str, dict] = request.app.get("node_meta", {})
    expose_agents = _token_ok(request)

    # Union of all known titles: files on disk + edge targets (dangling refs)
    all_titles: set = set(node_meta.keys())
    for src, targets in graph.adjacency.items():
        all_titles.add(src)
        all_titles.update(targets)

    nodes = []
    for title in sorted(all_titles):
        meta = node_meta.get(title, {"type": "note", "tags": []})
        nodes.append({
            "id": title,
            "title": title,
            "type": meta["type"],
            "tags": meta["tags"],
            "link_count": len(graph.adjacency.get(title, [])),
            "backlink_count": len(graph.backlinks.get(title, set())),
            "agents": _interactions.get(title, {}) if expose_agents else {},
        })

    links = []
    for source, targets in graph.adjacency.items():
        for target in targets:
            links.append({"source": source, "target": target})

    return web.json_response({
        "nodes": nodes,
        "links": links,
        "agent_colors": AGENT_COLORS,
    })


# ── NEXUS UI static serving ───────────────────────────────────────────────────

_NEXUS_UI_DIR = Path(__file__).parent / "nexus_ui"


async def handle_nexus_ui(request: web.Request) -> web.Response:
    """Serve the nexus_ui/index.html graph visualization."""
    html_path = _NEXUS_UI_DIR / "index.html"
    if not html_path.exists():
        return web.Response(status=404, text="nexus_ui not found")
    return web.Response(
        text=html_path.read_text(encoding="utf-8"),
        content_type="text/html",
        charset="utf-8",
    )


async def handle_root_redirect(request: web.Request) -> web.Response:
    raise web.HTTPFound("/nexus_ui")


# ===========================================================================
# App factory + startup/shutdown
# ===========================================================================

async def on_startup(app: web.Application) -> None:
    kb_root: Path = app["kb_root"]
    kb_root.mkdir(parents=True, exist_ok=True)

    # Initialise Qdrant collection
    store: VectorStore = app["store"]
    store.ensure_collection(NEXUS_COLLECTION, VECTOR_DIMENSION)

    # Build in-memory knowledge graph
    graph: KnowledgeGraph = app["graph"]
    loop = asyncio.get_running_loop()
    await loop.run_in_executor(None, graph.build, kb_root)

    # Build lightweight node metadata cache (type + tags for every .md file)
    node_meta = await loop.run_in_executor(None, _build_node_meta, kb_root)
    app["node_meta"] = node_meta
    logger.info("[nexus/server] node_meta built — %d nodes", len(node_meta))

    # Load persisted agent interaction data
    _load_interactions()
    logger.info("[nexus/server] interactions loaded — %d tracked nodes", len(_interactions))

    logger.info("[nexus/server] ready — kb_root=%s", kb_root)


async def on_shutdown(app: web.Application) -> None:
    logger.info("[nexus/server] shutting down")


async def _drain_bg_tasks(app: web.Application) -> None:
    tasks = list(app.get("_bg_tasks") or ())
    for t in tasks:
        t.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)


def create_app(kb_root: Optional[Path] = None) -> web.Application:
    if kb_root is None:
        kb_root = Path(NEXUS_KB_PATH)

    store = get_vector_store(Path(MEMORY_DB_PATH))
    embedder = get_embedding_service()
    graph = get_graph()

    app = web.Application(middlewares=[auth_middleware])
    app["kb_root"] = kb_root
    app["store"] = store
    app["embedder"] = embedder
    app["graph"] = graph
    app["_bg_tasks"] = set()

    app.on_startup.append(on_startup)
    app.on_shutdown.append(on_shutdown)
    app.on_shutdown.append(_drain_bg_tasks)

    # Routes
    app.router.add_get("/", handle_root_redirect)
    app.router.add_get("/nexus_ui", handle_nexus_ui)
    app.router.add_get("/nexus_ui/", handle_nexus_ui)
    app.router.add_get("/api/graph", handle_get_graph)
    app.router.add_get("/health", handle_health)
    app.router.add_get("/api/nodes/search", handle_search)
    app.router.add_get("/api/tags/{tag}", handle_get_by_tag)
    app.router.add_post("/api/nodes", handle_create_node)
    app.router.add_post("/api/nodes/reembed", handle_reembed)
    app.router.add_get("/api/nodes/{title:.+}/backlinks", handle_get_backlinks)
    app.router.add_get("/api/nodes/{title:.+}/neighbors", handle_get_neighbors)
    app.router.add_get("/api/nodes/{title:.+}", handle_get_node)
    app.router.add_post("/api/nodes/{title:.+}/append", handle_append)
    app.router.add_post("/api/nodes/{title:.+}/link", handle_link)
    app.router.add_patch("/api/nodes/{title:.+}/frontmatter", handle_update_frontmatter)
    app.router.add_delete("/api/nodes/{title:.+}", handle_delete_node)

    return app


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(asctime)s  %(levelname)-8s  %(name)s  %(message)s",
    )
    app = create_app()
    web.run_app(app, host=NEXUS_HOST, port=NEXUS_PORT, print=logger.info)


if __name__ == "__main__":
    main()
