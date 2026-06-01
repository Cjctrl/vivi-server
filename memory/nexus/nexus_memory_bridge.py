"""
nexus/nexus_memory_bridge.py
AgentMemoryClient — the only interface agents use to read/write NEXUS.

All agents must import and use AgentMemoryClient.  No agent may access
Qdrant directly or read/write nexus/knowledge_base/ files directly.

Two surfaces:
    AgentMemoryClient   — synchronous (uses requests); for BaseAgent subclasses
                          running in thread-pool executors.
    AsyncAgentMemoryClient — async (uses aiohttp); for async contexts such as
                              the conductor, tests, or server-side tooling.

Both expose identical methods with the same signatures.
"""

from __future__ import annotations

import logging
import os
import threading
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

# Host/port are read straight from the environment (config.settings loads .env
# into os.environ, and every entrypoint imports settings before this module).
# Kept as a plain os.environ read — not a config.settings import — so importing
# the bridge never triggers settings' _required() checks at import time.
NEXUS_HOST = os.environ.get("NEXUS_HOST", "127.0.0.1")
NEXUS_PORT = os.environ.get("NEXUS_PORT", "7200")
NEXUS_BASE_URL = f"http://{NEXUS_HOST}:{NEXUS_PORT}"

# ---------------------------------------------------------------------------
# Thread-local agent context — set by AsyncAgentWrapper before each agent run
# so the bridge can tag every HTTP request with which agent made it.
# ---------------------------------------------------------------------------
_tl = threading.local()


def _set_agent(name: str) -> None:
    _tl.agent = name


def _get_agent() -> str:
    return getattr(_tl, "agent", "unknown")


def _nexus_token() -> str:
    """Shared secret the NEXUS server requires on mutating endpoints.

    Read lazily from settings so importing this module never forces config
    resolution at import time (settings marks NEXUS_SECRET as _required()).
    """
    from config.settings import NEXUS_SECRET
    return NEXUS_SECRET


# ===========================================================================
# Synchronous client  (used by agents)
# ===========================================================================

class AgentMemoryClient:
    """
    Synchronous HTTP client for the NEXUS gateway.

    All method calls block the calling thread.  Agents that run in the
    conductor's thread-pool executor should use this class directly.

    Example
    -------
    from nexus.nexus_memory_bridge import get_memory_client

    client = get_memory_client()
    node = client.get_node("memories/session_abc")
    """

    def __init__(self, base_url: str = NEXUS_BASE_URL, timeout: int = 15) -> None:
        import requests
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})

    def _agent_headers(self) -> dict:
        # X-Nexus-Token is required by the server on mutating routes; harmless
        # on GETs, so we attach it to every request rather than branch by verb.
        return {"X-Agent-Name": _get_agent(), "X-Nexus-Token": _nexus_token()}

    def _get(self, path: str, params: Optional[dict] = None) -> dict:
        import requests
        url = f"{self._base}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=self._timeout, headers=self._agent_headers())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise NexusUnavailableError(
                "NEXUS server is not running — start it with: python -m memory.nexus.server"
            )
        except requests.exceptions.HTTPError as exc:
            raise NexusAPIError(f"GET {path} failed: {exc.response.status_code} {exc.response.text}")

    def _post(self, path: str, body: dict) -> dict:
        import requests
        url = f"{self._base}{path}"
        try:
            resp = self._session.post(url, json=body, timeout=self._timeout, headers=self._agent_headers())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise NexusUnavailableError(
                "NEXUS server is not running — start it with: python -m memory.nexus.server"
            )
        except requests.exceptions.HTTPError as exc:
            raise NexusAPIError(f"POST {path} failed: {exc.response.status_code} {exc.response.text}")

    def _patch(self, path: str, body: dict) -> dict:
        import requests
        url = f"{self._base}{path}"
        try:
            resp = self._session.patch(url, json=body, timeout=self._timeout, headers=self._agent_headers())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise NexusUnavailableError(
                "NEXUS server is not running — start it with: python -m memory.nexus.server"
            )
        except requests.exceptions.HTTPError as exc:
            raise NexusAPIError(f"PATCH {path} failed: {exc.response.status_code} {exc.response.text}")

    def _delete(self, path: str) -> dict:
        import requests
        url = f"{self._base}{path}"
        try:
            resp = self._session.delete(url, timeout=self._timeout, headers=self._agent_headers())
            resp.raise_for_status()
            return resp.json()
        except requests.exceptions.ConnectionError:
            raise NexusUnavailableError(
                "NEXUS server is not running — start it with: python -m memory.nexus.server"
            )
        except requests.exceptions.HTTPError as exc:
            raise NexusAPIError(f"DELETE {path} failed: {exc.response.status_code} {exc.response.text}")

    # ------------------------------------------------------------------
    # Read API
    # ------------------------------------------------------------------

    def search(
        self,
        query: str,
        limit: int = 5,
        semantic: bool = True,
        fulltext: bool = True,
    ) -> List[Dict[str, Any]]:
        """
        Semantic + full-text search across all nodes.

        Returns a list of node dicts, each with _score and _match fields.
        """
        data = self._get(
            "/api/nodes/search",
            params={"q": query, "limit": limit, "semantic": str(semantic).lower(), "fulltext": str(fulltext).lower()},
        )
        return data.get("results", [])

    def get_node(self, title: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a node by its title/path (e.g. 'memories/session_abc').

        Returns None if the node does not exist.
        """
        try:
            return self._get(f"/api/nodes/{title}")
        except NexusAPIError as exc:
            if "404" in str(exc):
                return None
            raise

    def get_backlinks(self, title: str) -> List[str]:
        """Return titles of all nodes that have an edge pointing to *title*."""
        data = self._get(f"/api/nodes/{title}/backlinks")
        return data.get("backlinks", [])

    def get_by_tag(self, tag: str) -> List[Dict[str, Any]]:
        """Return all nodes tagged with *tag*."""
        data = self._get(f"/api/tags/{tag}")
        return data.get("nodes", [])

    def get_neighbors(self, title: str, depth: int = 1) -> List[str]:
        """
        Traverse edges outward from *title* up to *depth* hops.

        Returns a list of reachable node titles.
        """
        data = self._get(f"/api/nodes/{title}/neighbors", params={"depth": depth})
        return data.get("neighbors", [])

    # ------------------------------------------------------------------
    # Write API
    # ------------------------------------------------------------------

    def create_node(
        self,
        title: str,
        body: str,
        tags: Optional[List[str]] = None,
        node_type: str = "note",
        edges: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a new .md node in the knowledge base.

        The title doubles as the file path (e.g. 'session-recaps/2026-05-20').
        Returns the created node dict.
        """
        return self._post("/api/nodes", {
            "title": title,
            "body": body,
            "tags": tags or [],
            "type": node_type,
            "edges": edges or [],
        })

    def append(self, title: str, text: str) -> Dict[str, Any]:
        """Append *text* to an existing node without overwriting its body."""
        return self._post(f"/api/nodes/{title}/append", {"text": text})

    def update_frontmatter(self, title: str, fields: Dict[str, Any]) -> Dict[str, Any]:
        """
        Patch YAML frontmatter fields on an existing node.

        Fields are merged — only provided keys are updated.
        """
        return self._patch(f"/api/nodes/{title}/frontmatter", fields)

    def link(self, from_title: str, to_title: str) -> Dict[str, Any]:
        """Add a directed edge from *from_title* → *to_title*."""
        return self._post(f"/api/nodes/{from_title}/link", {"to": to_title})

    def delete_node(self, title: str) -> Dict[str, Any]:
        """Delete a node and remove its vectors from Qdrant."""
        return self._delete(f"/api/nodes/{title}")

    def reembed(self, file_path: str) -> Dict[str, Any]:
        """
        Trigger re-embedding for a specific node file path.

        Called automatically by file_watcher.js; agents rarely need this directly.
        """
        return self._post("/api/nodes/reembed", {"path": file_path})

    def is_available(self) -> bool:
        """Return True if the NEXUS server is reachable."""
        try:
            self._get("/health")
            return True
        except (NexusUnavailableError, NexusAPIError):
            return False


# ===========================================================================
# Async client  (used in async contexts)
# ===========================================================================

class AsyncAgentMemoryClient:
    """
    Async HTTP client for the NEXUS gateway (aiohttp).

    Use this in async contexts: the conductor, startup checks, server-side
    tooling, or anywhere you need non-blocking I/O.

    Always close the client when done: await client.close()
    """

    def __init__(self, base_url: str = NEXUS_BASE_URL, timeout: int = 15) -> None:
        self._base = base_url.rstrip("/")
        self._timeout = timeout
        self._session = None  # lazily created
        self._agent_name: str = "unknown"

    def set_agent(self, name: str) -> None:
        self._agent_name = name

    def _agent_headers(self) -> dict:
        return {"X-Agent-Name": self._agent_name, "X-Nexus-Token": _nexus_token()}

    async def _get_session(self):
        import aiohttp
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={"Content-Type": "application/json"}
            )
        return self._session

    async def close(self) -> None:
        if self._session and not self._session.closed:
            await self._session.close()

    async def _get(self, path: str, params: Optional[dict] = None) -> dict:
        import aiohttp
        session = await self._get_session()
        try:
            async with session.get(
                f"{self._base}{path}", params=params,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                headers=self._agent_headers(),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientConnectorError:
            raise NexusUnavailableError("NEXUS server is not running")
        except aiohttp.ClientResponseError as exc:
            raise NexusAPIError(f"GET {path} failed: {exc.status}")

    async def _post(self, path: str, body: dict) -> dict:
        import aiohttp
        session = await self._get_session()
        try:
            async with session.post(
                f"{self._base}{path}", json=body,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                headers=self._agent_headers(),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientConnectorError:
            raise NexusUnavailableError("NEXUS server is not running")
        except aiohttp.ClientResponseError as exc:
            raise NexusAPIError(f"POST {path} failed: {exc.status}")

    async def _patch(self, path: str, body: dict) -> dict:
        import aiohttp
        session = await self._get_session()
        try:
            async with session.patch(
                f"{self._base}{path}", json=body,
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                headers=self._agent_headers(),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientConnectorError:
            raise NexusUnavailableError("NEXUS server is not running")
        except aiohttp.ClientResponseError as exc:
            raise NexusAPIError(f"PATCH {path} failed: {exc.status}")

    async def _delete(self, path: str) -> dict:
        import aiohttp
        session = await self._get_session()
        try:
            async with session.delete(
                f"{self._base}{path}",
                timeout=aiohttp.ClientTimeout(total=self._timeout),
                headers=self._agent_headers(),
            ) as resp:
                resp.raise_for_status()
                return await resp.json()
        except aiohttp.ClientConnectorError:
            raise NexusUnavailableError("NEXUS server is not running")
        except aiohttp.ClientResponseError as exc:
            raise NexusAPIError(f"DELETE {path} failed: {exc.status}")

    # Read API (async mirrors of AgentMemoryClient)

    async def search(self, query: str, limit: int = 5, semantic: bool = True, fulltext: bool = True) -> List[Dict]:
        data = await self._get("/api/nodes/search", params={"q": query, "limit": limit, "semantic": str(semantic).lower(), "fulltext": str(fulltext).lower()})
        return data.get("results", [])

    async def get_node(self, title: str) -> Optional[Dict]:
        try:
            return await self._get(f"/api/nodes/{title}")
        except NexusAPIError as exc:
            if "404" in str(exc):
                return None
            raise

    async def get_backlinks(self, title: str) -> List[str]:
        data = await self._get(f"/api/nodes/{title}/backlinks")
        return data.get("backlinks", [])

    async def get_by_tag(self, tag: str) -> List[Dict]:
        data = await self._get(f"/api/tags/{tag}")
        return data.get("nodes", [])

    async def get_neighbors(self, title: str, depth: int = 1) -> List[str]:
        data = await self._get(f"/api/nodes/{title}/neighbors", params={"depth": depth})
        return data.get("neighbors", [])

    # Write API (async)

    async def create_node(self, title: str, body: str, tags: Optional[List[str]] = None, node_type: str = "note", edges: Optional[List[str]] = None) -> Dict:
        return await self._post("/api/nodes", {"title": title, "body": body, "tags": tags or [], "type": node_type, "edges": edges or []})

    async def append(self, title: str, text: str) -> Dict:
        return await self._post(f"/api/nodes/{title}/append", {"text": text})

    async def update_frontmatter(self, title: str, fields: Dict) -> Dict:
        return await self._patch(f"/api/nodes/{title}/frontmatter", fields)

    async def link(self, from_title: str, to_title: str) -> Dict:
        return await self._post(f"/api/nodes/{from_title}/link", {"to": to_title})

    async def delete_node(self, title: str) -> Dict:
        return await self._delete(f"/api/nodes/{title}")

    async def reembed(self, file_path: str) -> Dict:
        return await self._post("/api/nodes/reembed", {"path": file_path})

    async def is_available(self) -> bool:
        try:
            await self._get("/health")
            return True
        except (NexusUnavailableError, NexusAPIError):
            return False


# ===========================================================================
# Exceptions
# ===========================================================================

class NexusUnavailableError(RuntimeError):
    """Raised when the NEXUS server is unreachable."""


class NexusAPIError(RuntimeError):
    """Raised when the NEXUS server returns a non-2xx response."""


# ===========================================================================
# Module-level singleton (sync client)
# ===========================================================================

_client: Optional[AgentMemoryClient] = None
_client_lock = threading.Lock()


def get_memory_client(base_url: str = NEXUS_BASE_URL) -> AgentMemoryClient:
    """Return the shared singleton AgentMemoryClient."""
    global _client
    if _client is None:
        with _client_lock:
            if _client is None:
                _client = AgentMemoryClient(base_url=base_url)
    return _client
