"""
config/settings.py
V.I.V.I AI Conductor — Configuration
Hardware: Ryzen 9800X3D · RTX 5080 16GB VRAM · 64GB System RAM
NEXUS is the sole knowledge/memory layer (port 7200, nexus/knowledge_base/).
"""

from __future__ import annotations
import os
from pathlib import Path

# Repository root (config/ is one level below it). Used to anchor write roots.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

def _env(key: str, default: str) -> str:
    return os.getenv(key, default)

def _required(key: str) -> str:
    val = os.getenv(key)
    if not val:
        raise ValueError(f"Required environment variable {key!r} is not set — add it to .env")
    return val

def _int(key: str, default: int) -> int:
    return int(os.getenv(key, str(default)))

def _float(key: str, default: float) -> float:
    return float(os.getenv(key, str(default)))

def _bool(key: str, default: bool) -> bool:
    return os.getenv(key, str(default)).lower() == "true"


# =============================================================================
# MODELS
# Tier 1 — Persistent residents (always loaded, fit comfortably together in
#           16GB VRAM at Q4: ~2GB + ~4GB + ~0.5GB ≈ 6.5GB combined)
# =============================================================================

CONDUCTOR_MODEL     = _env("CONDUCTOR_MODEL",     "qwen3:8b-q4")
WEB_SEARCH_MODEL    = _env("WEB_SEARCH_MODEL",    "llama3.1:8b-q4")
EMBED_MODEL         = _env("EMBED_MODEL",         "nomic-embed-text")   # also KB_SEARCH_MODEL
KB_SEARCH_MODEL     = EMBED_MODEL                                        # alias — single source of truth
VAULT_SEARCH_MODEL  = _env("VAULT_SEARCH_MODEL",  EMBED_MODEL)           # embeddings-backed vault search (~0.5GB, Tier 1)

# Tier 2 — Hot-swappable specialists (loaded on demand, evicted when idle)
# ~7–8GB each at Q4 — swap in/out without exceeding MAX_VRAM_USAGE_GB
CODING_MODEL        = _env("CODING_MODEL",        "qwen2.5-coder:14b-q4")
REASONING_MODEL     = _env("REASONING_MODEL",     "deepseek-r1:14b-q4")
MATH_MODEL          = _env("MATH_MODEL",          "phi4:14b-q4")
REFLECTION_MODEL    = _env("REFLECTION_MODEL",    "deepseek-r1:14b-q4")
VISUAL_CONTEXT_MODEL= _env("VISUAL_CONTEXT_MODEL","qwen2.5vl:7b-q4")
GRAPH_TRAVERSAL_MODEL=_env("GRAPH_TRAVERSAL_MODEL","qwen2.5-coder:7b-q4")
TOOL_DISCOVERY_MODEL= _env("TOOL_DISCOVERY_MODEL","qwen2.5-coder:7b-q4")  # 7b-q4 (~4GB) — reuses the coder family for tool/intent matching

# Tier 3 — Cold storage (explicitly requested only; evict all tier-2 first)
# ~13–14GB at Q3 — barely fits solo; never load alongside another large model
HEAVY_CODING_MODEL  = _env("HEAVY_CODING_MODEL",  "qwen2.5-coder:32b-q3")
HEAVY_REASONING_MODEL=_env("HEAVY_REASONING_MODEL","deepseek-r1:32b-q3")


# =============================================================================
# VRAM MANAGEMENT
# 5080 has 16GB. Keep 2GB headroom for driver + KV cache spikes.
# 14GB usable across all resident + active models.
# =============================================================================

MAX_VRAM_USAGE_GB       = _float("MAX_VRAM_USAGE_GB",   14.0)
VRAM_HEADROOM_GB        = _float("VRAM_HEADROOM_GB",     2.0)
MODEL_LOAD_TIMEOUT      = _int(  "MODEL_LOAD_TIMEOUT",   30)
MODEL_UNLOAD_TIMEOUT    = _int(  "MODEL_UNLOAD_TIMEOUT", 10)

# Context windows — tuned for 16GB; 14B models can safely run 8k context
# without blowing VRAM. 32B models need shorter context to fit.
CONTEXT_LIMITS: dict[str, int] = {
    "7b_models":  _int("CTX_7B",  8192),
    "14b_models": _int("CTX_14B", 8192),
    "32b_models": _int("CTX_32B", 4096),
}


# =============================================================================
# VECTOR / EMBEDDING
# nomic-embed-text produces 768-dim vectors.
# Qdrant is configured to keep the full index in RAM (see memory settings).
# =============================================================================

VECTOR_DIMENSION    = _int("VECTOR_DIMENSION", 768)
SIMILARITY_THRESHOLD= _float("SIMILARITY_THRESHOLD", 0.5)


# =============================================================================
# PATHS
# =============================================================================

NEXUS_KB_PATH           = _env("NEXUS_KB_PATH",       "./nexus/knowledge_base")
MEMORY_DB_PATH          = _env("MEMORY_DB_PATH",      "./memory/vivi_db")
EPISODIC_DB_PATH        = _env("EPISODIC_DB_PATH",    "./memory/episodic_db")
SCHOOL_DB_PATH          = _env("SCHOOL_DB_PATH",      "./db/school.db")
SANDBOX_DIR             = _env("SANDBOX_DIR",          "./sandbox")
WORKSPACE_ROOT          = _env("WORKSPACE_ROOT",       NEXUS_KB_PATH or "./")
LOG_FILE                = _env("LOG_FILE",             "conductor.log")

# Deprecated — kept for import compatibility only; do not use in new code
SEMANTIC_MEMORY_DB_PATH = _env("SEMANTIC_MEMORY_DB_PATH", "./memory/semantic_search_db")


# =============================================================================
# ZIM KNOWLEDGE BASE  (memory/zim_kb/)
# Offline knowledge retrieval over ZIM archives. Distinct from memory/nexus/
# (the Qdrant-backed VIVI knowledge graph). All data lives on the memory disk
# pointed to by VIVI_MEMDSK_PATH. In production set VIVI_MEMDSK_PATH to the
# actual mount (e.g. D:/vivi-memdsk); the default below is a local dev path
# under the repo so the system runs without the disk mounted.
# =============================================================================

VIVI_MEMDSK_PATH       = _env("VIVI_MEMDSK_PATH",       str(PROJECT_ROOT / "memory" / "zim_kb_data"))
ZIM_KB_ZIM_DIR         = _env("ZIM_KB_ZIM_DIR",         str(Path(VIVI_MEMDSK_PATH) / "zim"))
ZIM_KB_MARKDOWN_DIR    = _env("ZIM_KB_MARKDOWN_DIR",    str(Path(VIVI_MEMDSK_PATH) / "markdown_cache"))
ZIM_KB_EMBEDDINGS_DIR  = _env("ZIM_KB_EMBEDDINGS_DIR",  str(Path(VIVI_MEMDSK_PATH) / "embeddings"))
ZIM_KB_METADATA_DIR    = _env("ZIM_KB_METADATA_DIR",    str(Path(VIVI_MEMDSK_PATH) / "metadata"))
ZIM_KB_INDEX_DB        = _env("ZIM_KB_INDEX_DB",        str(Path(ZIM_KB_METADATA_DIR) / "nexus_index.sqlite"))


# =============================================================================
# SCHOOL / CALENDAR INTEGRATIONS
# Credentials must be set in environment — never hardcoded here.
# =============================================================================

POWERSCHOOL_URL      = _env("POWERSCHOOL_URL",      "")
POWERSCHOOL_USERNAME = _env("POWERSCHOOL_USERNAME", "")
POWERSCHOOL_PASSWORD = _env("POWERSCHOOL_PASSWORD", "")


# =============================================================================
# AGENT RUNTIME
# ThreadPoolExecutor in AsyncAgentWrapper should use AGENT_THREAD_WORKERS.
# 9800X3D has 16 cores / 16 threads — 12 leaves headroom for OS + Ollama.
# =============================================================================

MAX_STEPS            = _int(  "MAX_STEPS",           10)
DEFAULT_TIMEOUT      = _int(  "DEFAULT_TIMEOUT",     30)
AGENT_THREAD_WORKERS = _int(  "AGENT_THREAD_WORKERS", 12)  # size the executor here


# =============================================================================
# OLLAMA CLIENT
# 120s timeout is safe for 32B cold loads on the 5080.
# Circuit breaker trips after 5 consecutive failures.
# =============================================================================

OLLAMA_MAX_RETRIES          = _int("OLLAMA_MAX_RETRIES",          3)
OLLAMA_TIMEOUT_SECONDS      = _int("OLLAMA_TIMEOUT_SECONDS",      120)
OLLAMA_CIRCUIT_THRESHOLD    = _int("OLLAMA_CIRCUIT_THRESHOLD",    5)
OLLAMA_CIRCUIT_RESET_SECONDS= _int("OLLAMA_CIRCUIT_RESET_SECONDS",30)


# =============================================================================
# MEMORY / CACHE SIZES
# Generous limits — 64GB system RAM means no reason to be stingy.
# =============================================================================

SUMMARIZATION_CACHE_MAX  = _int("SUMMARIZATION_CACHE_MAX",  2_000)  # was 100
KEYWORD_SEARCH_MAX_BYTES = _int("KEYWORD_SEARCH_MAX_BYTES", 20_971_520)  # 20MB, was 5MB
KB_INDEX_MAX_BYTES       = _int("KB_INDEX_MAX_BYTES",       10_485_760)  # 10MB per file


# =============================================================================
# SANDBOX SECURITY
# =============================================================================

SANDBOX_NETWORK_DISABLED = _bool("SANDBOX_NETWORK_DISABLED", True)
SANDBOX_ROOT_DISABLED    = _bool("SANDBOX_ROOT_DISABLED",    True)


# =============================================================================
# MONITORING
# VRAM_CHECK_INTERVAL at 1s is fine — 5080 NVML queries are cheap.
# Thermal throttle at 83°C gives 7° margin before the 5080's 90°C TjMax.
# =============================================================================

ENABLE_VRAM_MONITORING  = _bool( "ENABLE_VRAM_MONITORING",  True)
VRAM_CHECK_INTERVAL     = _float("VRAM_CHECK_INTERVAL",      1.0)
THERMAL_THROTTLE_TEMP   = _float("THERMAL_THROTTLE_TEMP",   83.0)  # was 80, bumped for 5080
LOG_LEVEL               = _env(  "LOG_LEVEL",               "INFO")


# =============================================================================
# RECAP
# =============================================================================

RECAP_PROSE_ENABLED = _bool("RECAP_PROSE_ENABLED", True)


# =============================================================================
# VISION / VISUAL SCANNER
# llava:13b primary; fall back to lighter models already on disk.
# VISION_TIMEOUT is slow by design — multimodal inference takes time.
# =============================================================================

VISION_MODEL    = _env("VISION_MODEL",   "llava:13b")
VISION_FALLBACK: list[str] = ["llava", "moondream"]
VISION_TIMEOUT  = _int("VISION_TIMEOUT", 60)

PHOTO_MEMORY_CACHE_SIZE = _int("PHOTO_MEMORY_CACHE_SIZE", 50)
PHOTO_MEMORY_CACHE_TTL  = _int("PHOTO_MEMORY_CACHE_TTL",  300)  # seconds


# =============================================================================
# CAPABILITY DISCOVERY
# =============================================================================

CAPABILITY_REGISTRY_PATH = _env("CAPABILITY_REGISTRY_PATH", "./data/capability_registry.json")
CAPABILITY_CACHE_TTL     = _int("CAPABILITY_CACHE_TTL", 86400)  # seconds; 0 = always rescan


# =============================================================================
# OVERLAY (JARVIS-style HUD)
# Port 7300 — aiohttp WebSocket server bridging the pywebview frontend to the conductor.
# CAPTURE_INTERVAL: seconds between background screen grabs (0 = disabled).
# WHISPER_MODEL: faster-whisper model size; "base.en" (~150MB) is CPU-safe.
# =============================================================================

OVERLAY_PORT                 = _int(  "OVERLAY_PORT",               7300)
OVERLAY_CAPTURE_INTERVAL     = _float("OVERLAY_CAPTURE_INTERVAL",    5.0)
OVERLAY_WS_METRICS_INTERVAL  = _float("OVERLAY_WS_METRICS_INTERVAL", 5.0)
OVERLAY_WHISPER_MODEL        = _env(  "OVERLAY_WHISPER_MODEL",      "base.en")
NEXUS_PORT                   = _int(  "NEXUS_PORT",                  7200)

# WS_SECRET — shared secret for the overlay WebSocket HMAC challenge-response
# auth gate (see overlay/overlay_server.py ws_handler). REQUIRED, no default:
# the Origin check on port 7300 is NOT authentication, so destructive WS
# commands (app_launch_request, confirm_file_write, open_in_explorer,
# open_in_vscode, notes_save, shutdown) are rejected until a client proves it
# holds this secret. Generate with:
#   python -c "import secrets; print(secrets.token_hex(32))"
WS_SECRET = _required("WS_SECRET")

# NEXUS_SECRET — shared secret gating the mutating NEXUS HTTP endpoints
# (POST/PATCH/DELETE on memory/nexus/server.py, port 7200). REQUIRED, no
# default: the server binds to localhost only, but any local process can reach
# it, so writes/deletes must prove they hold this secret via either an
# `Authorization: Bearer <token>` or `X-Nexus-Token: <token>` header. GET
# routes stay open (read-only). Mirrors the WS_SECRET handshake pattern.
# Generate with:
#   python -c "import secrets; print(secrets.token_hex(32))"
NEXUS_SECRET = _required("NEXUS_SECRET")

# Manifestation system — dynamic UI projection layer
MANIFESTATION_AUTO_DISSOLVE_MS   = _int( "MANIFESTATION_AUTO_DISSOLVE_MS",   15000)
MANIFESTATION_NOTICE_DISSOLVE_MS = _int( "MANIFESTATION_NOTICE_DISSOLVE_MS",  7000)
MANIFESTATION_URGENCY_SCAN       = _bool("MANIFESTATION_URGENCY_SCAN",         True)
MANIFESTATION_SPATIAL_AGENTS     = _bool("MANIFESTATION_SPATIAL_AGENTS",       True)


# =============================================================================
# JARVIS ENHANCEMENTS
# Persona, personal facts memory, and proactivity scheduler settings.
# =============================================================================

# Personal facts extraction (runs fire-and-forget after every task)
JARVIS_FACTS_EXTRACT_ENABLED = _bool("JARVIS_FACTS_EXTRACT_ENABLED", True)

# Proactivity scheduler
JARVIS_MORNING_BRIEFING_HOUR    = _int(  "JARVIS_MORNING_BRIEFING_HOUR",    9)   # 9 AM
JARVIS_BREAK_INTERVAL_HOURS     = _float("JARVIS_BREAK_INTERVAL_HOURS",    2.0)  # suggest break after 2h
JARVIS_CALENDAR_REMINDER_MINUTES= _int(  "JARVIS_CALENDAR_REMINDER_MINUTES", 15)  # warn 15 min before events


# =============================================================================
# STUDY MODE
# STUDY_SESSION_TIMEOUT_MINS: inactivity window before a session expires.
# CHROME_DEBUG_PORT: Chrome remote debugging port for CDP-based doc extraction.
# =============================================================================

STUDY_SESSION_TIMEOUT_MINS = _int("STUDY_SESSION_TIMEOUT_MINS", 30)
CHROME_DEBUG_PORT          = _int("CHROME_DEBUG_PORT",          9222)

# SECURITY: Chrome's --remote-debugging-port opens an UNAUTHENTICATED CDP
# endpoint on localhost. Any local process (or a malicious web page via DNS
# rebinding) can drive the browser, read every open tab, and exfiltrate
# cookies/sessions through it. It is therefore OFF by default. Enable it only
# when you actively need VIVI to read Google Docs / browser PDFs, and prefer
# launching that Chrome instance with a dedicated throwaway profile.
ENABLE_CHROME_DEBUGGING    = _bool("ENABLE_CHROME_DEBUGGING",   False)


# =============================================================================
# GAME SESSION MODE
# TIMEOUT_MINS: keep session alive N minutes after game closes (alt-tab grace).
# SCREENSHOT_INTERVAL_TICKS: analyze screen every Nth screen_tick (5 ticks = 25s).
# ALERT_COOLDOWN_SECS: minimum seconds between repeated danger alerts.
# SEARCH_CACHE_MAX: max cached wiki/guide lookups per session (FIFO eviction).
# =============================================================================

GAME_SESSION_TIMEOUT_MINS       = _int("GAME_SESSION_TIMEOUT_MINS",       10)
GAME_SCREENSHOT_INTERVAL_TICKS  = _int("GAME_SCREENSHOT_INTERVAL_TICKS",   5)
GAME_ALERT_COOLDOWN_SECS        = _int("GAME_ALERT_COOLDOWN_SECS",        60)
GAME_SEARCH_CACHE_MAX           = _int("GAME_SEARCH_CACHE_MAX",           30)


# =============================================================================
# CODE SESSION MODE
# Stateful multi-turn coding session anchored to an open editor file.
# =============================================================================

CODE_SESSION_TIMEOUT_MINS    = _int( "CODE_SESSION_TIMEOUT_MINS",    45)
CODE_SESSION_MAX_OPEN_FILES  = _int( "CODE_SESSION_MAX_OPEN_FILES",  10)
CODE_REFLECTION_ENABLED      = _bool("CODE_REFLECTION_ENABLED",      True)
CODE_SEARCH_ON_UNKNOWN_ERROR = _bool("CODE_SEARCH_ON_UNKNOWN_ERROR", True)

# The code session edits the user's open editor files, which live OUTSIDE the
# NEXUS knowledge base. file_write_agent is intentionally KB-only (its root is
# NEXUS_KB_PATH) and must not be used for these writes — the overlay writes them
# directly, confined to this root via resolve() + is_relative_to(). Defaults to
# the VIVI project root; set OVERLAY_CODE_WRITE_ROOT to a parent directory if you
# edit files from several projects through the overlay.
OVERLAY_CODE_WRITE_ROOT      = _env("OVERLAY_CODE_WRITE_ROOT", str(PROJECT_ROOT))


# =============================================================================
# BLENDER SESSION MODE
# TIMEOUT_MINS: keep session alive N minutes after Blender closes/alt-tabs.
# SCRIPTS_DIR: where generated bpy scripts are written for manual or auto-run.
# SCREENSHOT_INTERVAL_TICKS: analyze viewport every Nth screen_tick (4 × 5s = 20s).
# HTTP_API_PORT: Blender 4.2+ local REST API port (--enable-http-api).
# ALERT_COOLDOWN_SECS: minimum seconds between repeated viewport error alerts.
# =============================================================================

BLENDER_SESSION_TIMEOUT_MINS      = _int(  "BLENDER_SESSION_TIMEOUT_MINS",       15)
BLENDER_SCRIPTS_DIR               = _env(  "BLENDER_SCRIPTS_DIR",                "./blender_scripts")
BLENDER_SCREENSHOT_INTERVAL_TICKS = _int(  "BLENDER_SCREENSHOT_INTERVAL_TICKS",   4)
BLENDER_HTTP_API_PORT             = _int(  "BLENDER_HTTP_API_PORT",             8080)
BLENDER_HTTP_API_ENABLED          = _bool( "BLENDER_HTTP_API_ENABLED",           True)
BLENDER_ALERT_COOLDOWN_SECS       = _int(  "BLENDER_ALERT_COOLDOWN_SECS",         90)