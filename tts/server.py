"""
tts/server.py
aiohttp gateway for the V.I.V.I distributed TTS service (IndexTTS2).

Binds TTS_HOST:TTS_PORT (default 127.0.0.1:7600). The brain (vivi-brain, a
separate box) POSTs text here, gets raw WAV bytes back, and streams them to
clients itself. This host is HEADLESS — the service only ever returns audio
bytes and never plays sound locally.

Style reference: memory/nexus/server.py (aiohttp app factory + shared-secret
auth middleware + structlog). This service differs in three ways: auth is
Bearer-ONLY and required on every real route (not just mutations), the body is
size-capped, and the synth response is binary audio/wav rather than JSON.

HTTP contract:
    POST /tts
        Headers: Authorization: Bearer {TTS_SECRET}; Content-Type: application/json
        Body:    {"text": str,
                  "emo_vector": [8 floats] | null,
                  "voice_id": str (default "vivi"),
                  "format": "wav"}
        200  ->  Content-Type: audio/wav, body = raw WAV bytes
        4xx/5xx -> application/json {"error": str}
    GET /health
        -> {"status": "ok", "model_loaded": bool, "voices": [...]}  (no auth)

Start:
    python -m tts.server        # or: python -m tts
"""

from __future__ import annotations

import asyncio
import hmac
import json
from typing import Optional

from aiohttp import web

from core.logging_setup import configure_logging, get_logger
from config.settings import (
    TTS_DEVICE,
    TTS_HOST,
    TTS_PORT,
    TTS_SECRET,
    VIVI_VOICE_REF,
)
from tts.engine import ViviTTS, TTSEngineError, validate_emo_vector

logger = get_logger("tts.server")

# Reject oversized bodies early. TTS payloads are short text + an 8-float list;
# 256KB is enormous headroom and stops a client from streaming a huge body at us
# (the brain can comfortably chunk longer narration into multiple requests).
MAX_BODY_BYTES = 256 * 1024

# Public, unauthenticated routes (liveness only — never reveals model internals
# beyond loaded-state + voice ids, mirroring NEXUS /health staying open).
_OPEN_PATHS: frozenset[str] = frozenset({"/health"})


# ===========================================================================
# Authentication — Bearer {TTS_SECRET}, timing-safe
# ===========================================================================

def _extract_bearer(request: web.Request) -> str:
    """Return the token from `Authorization: Bearer <token>`, else ""."""
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        return auth[len("Bearer "):].strip()
    return ""


def _token_ok(request: web.Request) -> bool:
    """True when the request carries the valid TTS shared secret.

    compare_digest is timing-safe; both operands must be non-empty. TTS_SECRET
    falls back to NEXUS_SECRET in config (never empty in a valid deployment), so
    there is no "auth disabled" hole here.
    """
    provided = _extract_bearer(request)
    return bool(provided) and bool(TTS_SECRET) and hmac.compare_digest(provided, TTS_SECRET)


@web.middleware
async def auth_middleware(request: web.Request, handler):
    """Gate every route except /health behind the Bearer secret.

    Unlike NEXUS (which leaves reads open), this service has exactly one real
    endpoint and it does GPU work, so we require the token on it unconditionally.
    """
    if request.path not in _OPEN_PATHS and not _token_ok(request):
        logger.warning("auth_rejected", method=request.method, path=request.path)
        return web.json_response(
            {"error": "Unauthorized — valid 'Authorization: Bearer <TTS_SECRET>' header required"},
            status=401,
        )
    return await handler(request)


# ===========================================================================
# Route handlers
# ===========================================================================

async def handle_health(request: web.Request) -> web.Response:
    """GET /health — liveness + whether the model is warm yet. Open (no auth)."""
    engine: ViviTTS = request.app["engine"]
    return web.json_response(
        {
            "status": "ok",
            "model_loaded": engine.model_loaded,
            "voices": engine.voices,
        }
    )


async def handle_tts(request: web.Request) -> web.Response:
    """POST /tts — synthesize text to WAV bytes (Bearer-gated).

    Validation failures (bad JSON, missing/blank text, bad emo_vector, wrong
    format) return 400 with {"error": ...}. Engine/model failures return 500
    with {"error": ...}. Success returns raw audio/wav bytes.
    """
    # Body-size cap. Prefer the declared Content-Length, but also guard against a
    # client that lies about it by reading at most MAX_BODY_BYTES + 1.
    if request.content_length is not None and request.content_length > MAX_BODY_BYTES:
        return web.json_response(
            {"error": f"Request body too large (>{MAX_BODY_BYTES} bytes)"}, status=413
        )
    raw = await request.content.read(MAX_BODY_BYTES + 1)
    if len(raw) > MAX_BODY_BYTES:
        return web.json_response(
            {"error": f"Request body too large (>{MAX_BODY_BYTES} bytes)"}, status=413
        )

    try:
        data = json.loads(raw.decode("utf-8"))
    except Exception:
        return web.json_response({"error": "Invalid JSON body"}, status=400)
    if not isinstance(data, dict):
        return web.json_response({"error": "JSON body must be an object"}, status=400)

    text = data.get("text")
    if not isinstance(text, str) or not text.strip():
        return web.json_response({"error": "text is required and must be a non-empty string"}, status=400)

    fmt = data.get("format", "wav")
    if fmt != "wav":
        return web.json_response({"error": f"unsupported format {fmt!r}; only 'wav' is supported"}, status=400)

    # voice_id is accepted for forward-compat; today there is one cloned ref
    # voice, so anything other than the configured id is rejected explicitly
    # rather than silently substituted.
    engine: ViviTTS = request.app["engine"]
    voice_id = data.get("voice_id", engine.voice_id)
    if voice_id not in engine.voices:
        return web.json_response(
            {"error": f"unknown voice_id {voice_id!r}; available: {engine.voices}"}, status=400
        )

    # Validate the emotion vector HERE so a malformed one is unambiguously a 400
    # (a client error) — separate from the engine/model failures below, which are
    # server-side 500s. The engine re-validates defensively, but doing it up front
    # keeps the status mapping clean and avoids loading the model on bad input.
    emo_vector = data.get("emo_vector", None)
    try:
        validate_emo_vector(emo_vector)
    except TTSEngineError as exc:
        return web.json_response({"error": str(exc)}, status=400)

    loop = asyncio.get_running_loop()
    try:
        # Synthesis is blocking + GPU-bound; run it off the event loop. The
        # engine serialises concurrent synths internally (single-stream model).
        wav_bytes = await loop.run_in_executor(
            None, engine.synthesize, text, emo_vector
        )
    except TTSEngineError as exc:
        # Reaches here only for server-side failures (missing reference clip,
        # model load/inference error) — input was already validated above.
        msg = str(exc)
        logger.error("synthesis_failed", error=msg)
        return web.json_response({"error": msg}, status=500)
    except Exception as exc:  # pragma: no cover - unexpected
        logger.error("synthesis_unexpected_error", error=str(exc))
        return web.json_response({"error": "internal synthesis error"}, status=500)

    return web.Response(
        body=wav_bytes,
        content_type="audio/wav",
        headers={"Content-Disposition": 'inline; filename="vivi_tts.wav"'},
    )


# ===========================================================================
# App factory + startup
# ===========================================================================

def _build_engine() -> ViviTTS:
    """Construct the (lazy) ViviTTS engine from config. Cheap — no torch here."""
    return ViviTTS(
        reference_audio=VIVI_VOICE_REF,
        device=TTS_DEVICE,
        use_fp16=True,
        use_cuda_kernel=True,
        max_text_tokens_per_segment=80,
        voice_id="vivi",
    )


async def on_startup(app: web.Application) -> None:
    engine: ViviTTS = app["engine"]
    logger.info(
        "tts_server_ready",
        host=TTS_HOST,
        port=TTS_PORT,
        device=TTS_DEVICE,
        reference_audio=str(engine.reference_audio),
        model_loaded=engine.model_loaded,
        note="model loads lazily on first /tts call",
    )


def create_app(engine: Optional[ViviTTS] = None) -> web.Application:
    """Build the aiohttp application (engine optional for tests)."""
    app = web.Application(
        middlewares=[auth_middleware],
        client_max_size=MAX_BODY_BYTES + 1024,  # belt-and-suspenders body cap
    )
    app["engine"] = engine if engine is not None else _build_engine()
    app.on_startup.append(on_startup)

    app.router.add_get("/health", handle_health)
    app.router.add_post("/tts", handle_tts)
    return app


def main() -> None:
    configure_logging()
    app = create_app()
    web.run_app(app, host=TTS_HOST, port=TTS_PORT, print=lambda *a, **k: logger.info("listening", addr=f"{TTS_HOST}:{TTS_PORT}"))


if __name__ == "__main__":
    main()
