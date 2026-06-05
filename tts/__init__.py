"""
tts/  —  V.I.V.I distributed text-to-speech (IndexTTS2 microservice).

This package runs on the HEADLESS memory box (RTX 3060 12GB) and exposes a tiny
HTTP service the brain (vivi-brain, a separate machine) calls to turn text into
spoken WAV bytes. The brain streams that audio to clients itself; this box has no
speakers and NEVER plays audio locally — it only ever returns bytes.

Layout:
    tts/engine.py   ViviTTS — a lazy-loading wrapper around IndexTTS2. torch and
                    indextts are imported INSIDE the synth call, so importing this
                    package is safe on a machine without the GPU model present.
    tts/server.py   aiohttp app: POST /tts (Bearer-gated) + GET /health.
    tts/__main__.py `python -m tts.server` / `python -m tts` both start it.

Import safety is deliberate: nothing at module top pulls torch/indextts, so the
rest of the repo (and the test suite) can `import tts.server` without the heavy
stack installed. See tts/README.md for the install + deploy steps.
"""

from __future__ import annotations

__all__ = ["ViviTTS", "TTSEngineError"]


def __getattr__(name: str):
    # Lazily forward the public names to tts.engine so that
    # `from tts import ViviTTS` works without importing engine (and therefore
    # without any chance of dragging torch in) until it is actually referenced.
    if name in __all__:
        from tts import engine

        return getattr(engine, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
