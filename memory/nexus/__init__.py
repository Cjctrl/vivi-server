"""
nexus/ — NEXUS knowledge and memory layer for V.I.V.I.

All agents must interact with the knowledge base exclusively through
AgentMemoryClient (nexus_memory_bridge.py), which speaks to the NEXUS
HTTP server running on port 7200.  No agent may access Qdrant directly.

Folder layout:
    nexus/knowledge_base/   — .md nodes, human-readable at rest
    nexus/server.py         — aiohttp HTTP gateway (port 7200)
    nexus/nexus_memory_bridge.py — AgentMemoryClient used by all agents
    nexus/graph.py          — edge traversal and backlink utilities
    nexus/file_watcher.js   — Node.js watcher; re-embeds nodes on change
"""
