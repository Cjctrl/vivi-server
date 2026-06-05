"""
tts/engine.py
ViviTTS — a thin, import-safe wrapper around IndexTTS2 (indextts.infer_v2).

Design constraints (see tts/__init__.py and tts/README.md):

  * IMPORT-SAFE WITHOUT TORCH. torch and indextts are imported INSIDE the synth
    path, never at module top, so this module imports cleanly on a machine that
    has neither installed (the test box, CI, the brain). The model is LAZY-loaded
    on the first synth call.
  * HEADLESS / RETURN-ONLY. Synthesis writes an in-memory WAV and returns the raw
    bytes. Nothing here ever opens an audio device or plays sound — this box has
    no speakers.
  * SINGLE-STREAM. IndexTTS2 is autoregressive and not concurrency-safe, so every
    inference is serialised behind a threading.Lock. The aiohttp server runs the
    blocking call in a thread-pool executor and relies on this lock for safety.
  * PEAK-VRAM CONSCIOUS. The model is built FP16 with the CUDA kernel enabled and
    a low max_text_tokens_per_segment so a long utterance is chunked rather than
    spiking VRAM (this card also holds NEXUS' embed model + the 8B summarizer —
    see the Scenario-C budget in config/settings.py).

The IndexTTS2 Python API can drift between releases; the constructor kwargs and
the infer() signature used here are the ones documented for IndexTTS-2 at the
time of writing and are flagged "verify against the installed version" in the
README. If a kwarg is rejected, adjust _build_model()/_infer_to_file() rather
than the public interface.
"""

from __future__ import annotations

import io
import threading
import wave
from pathlib import Path
from typing import List, Optional, Sequence

from core.logging_setup import get_logger

logger = get_logger("tts.engine")


# ---------------------------------------------------------------------------
# emo_vector contract (mirrors the HTTP contract in tts/server.py)
#   layout: [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm]
#   each component 0.0 .. EMO_COMPONENT_MAX, sum <= EMO_SUM_MAX
#   None  =>  neutral default (no emotion vector handed to the model)
# ---------------------------------------------------------------------------
EMO_VECTOR_LEN: int = 8
EMO_COMPONENT_MAX: float = 1.4
EMO_SUM_MAX: float = 0.8
EMO_LABELS: tuple[str, ...] = (
    "happy",
    "angry",
    "sad",
    "afraid",
    "disgusted",
    "melancholic",
    "surprised",
    "calm",
)


class TTSEngineError(RuntimeError):
    """Raised for any engine-level failure that should surface as a clean error.

    The server maps this to a JSON error response rather than a 500 stack trace,
    so the message is intended to be caller-facing (e.g. a missing reference
    voice, an invalid emotion vector, or a model that failed to load).
    """


def validate_emo_vector(emo_vector: Optional[Sequence[float]]) -> Optional[List[float]]:
    """Validate and normalise an emotion vector.

    Returns a fresh list of 8 floats, or None for the neutral default. Raises
    TTSEngineError with a descriptive message on any contract violation so the
    server can return a 400. Kept as a module function (not a method) so the
    server can reject bad input BEFORE touching / loading the model.
    """
    if emo_vector is None:
        return None

    if isinstance(emo_vector, (str, bytes)) or not isinstance(emo_vector, Sequence):
        raise TTSEngineError("emo_vector must be a list of 8 numbers or null")

    if len(emo_vector) != EMO_VECTOR_LEN:
        raise TTSEngineError(
            f"emo_vector must have exactly {EMO_VECTOR_LEN} components "
            f"({', '.join(EMO_LABELS)}); got {len(emo_vector)}"
        )

    out: List[float] = []
    for i, raw in enumerate(emo_vector):
        if isinstance(raw, bool) or not isinstance(raw, (int, float)):
            raise TTSEngineError(
                f"emo_vector[{i}] ({EMO_LABELS[i]}) must be a number, got {type(raw).__name__}"
            )
        val = float(raw)
        if val < 0.0 or val > EMO_COMPONENT_MAX:
            raise TTSEngineError(
                f"emo_vector[{i}] ({EMO_LABELS[i]})={val} out of range "
                f"0.0..{EMO_COMPONENT_MAX}"
            )
        out.append(val)

    total = sum(out)
    if total > EMO_SUM_MAX:
        raise TTSEngineError(
            f"emo_vector components sum to {total:.3f}, exceeding the max {EMO_SUM_MAX}"
        )
    return out


class ViviTTS:
    """Lazy IndexTTS2 wrapper.

    Construct it cheaply at process start (no torch needed); the heavy model is
    built on the FIRST synthesize() call and then kept warm. All inference is
    serialised behind an instance lock because IndexTTS2 is single-stream.
    """

    def __init__(
        self,
        *,
        reference_audio: str | Path,
        device: str = "cuda:0",
        use_fp16: bool = True,
        use_cuda_kernel: bool = True,
        max_text_tokens_per_segment: int = 80,
        voice_id: str = "vivi",
        model_dir: str | Path = "checkpoints",
        config_path: Optional[str | Path] = None,
    ) -> None:
        # Stash config only — DO NOT import torch / build the model here. The
        # whole point is that constructing ViviTTS stays import-safe and cheap.
        self.reference_audio = Path(reference_audio)
        self.device = device
        self.use_fp16 = use_fp16
        self.use_cuda_kernel = use_cuda_kernel
        self.max_text_tokens_per_segment = int(max_text_tokens_per_segment)
        self.voice_id = voice_id
        self.model_dir = Path(model_dir)
        # IndexTTS2 ships its config as checkpoints/config.yaml; allow an override.
        self.config_path = Path(config_path) if config_path else self.model_dir / "config.yaml"

        self._model = None  # the IndexTTS2 instance, built lazily
        self._lock = threading.Lock()  # serialise inference (single-stream model)
        self._load_lock = threading.Lock()  # serialise the one-time model build

    # -- introspection -----------------------------------------------------

    @property
    def model_loaded(self) -> bool:
        """True once the IndexTTS2 model has been built (after first synth)."""
        return self._model is not None

    @property
    def voices(self) -> List[str]:
        """Voice ids this engine can render. Currently the single cloned ref voice."""
        return [self.voice_id]

    # -- model lifecycle ---------------------------------------------------

    def _ensure_reference_audio(self) -> None:
        """Fail clearly (not on import, not with a torch traceback) if the
        reference voice clip is missing. Raised lazily so a misconfigured path
        only breaks synthesis, never the import or the /health probe."""
        if not self.reference_audio.is_file():
            raise TTSEngineError(
                f"Reference voice clip not found: {self.reference_audio}. "
                "Create a 5-15s clean mono WAV at this path (set VIVI_VOICE_REF) — "
                "IndexTTS2 clones it for zero-shot synthesis. See tts/README.md."
            )

    def _build_model(self):
        """Import torch/indextts and construct IndexTTS2 (heavy, one-time).

        Imports live HERE so the module stays importable without the stack. Any
        failure is wrapped in TTSEngineError so the server returns a clean error
        instead of leaking the import/CUDA traceback to the caller.
        """
        try:
            # Imported lazily and intentionally unused beyond the availability
            # check — IndexTTS2 needs torch present; this gives a precise error
            # if it is not, before the (longer) model load.
            import torch  # noqa: F401
        except Exception as exc:  # pragma: no cover - depends on host
            raise TTSEngineError(
                "PyTorch is not installed in this environment — install the CUDA "
                "build (see tts/README.md) before starting the TTS service."
            ) from exc

        try:
            from indextts.infer_v2 import IndexTTS2
        except Exception as exc:  # pragma: no cover - depends on host
            raise TTSEngineError(
                "indextts is not installed/importable — clone index-tts and run "
                "`uv sync --all-extras` (see tts/README.md)."
            ) from exc

        if not self.config_path.is_file():
            raise TTSEngineError(
                f"IndexTTS2 config not found: {self.config_path}. Download the "
                "checkpoints (hf download IndexTeam/IndexTTS-2 --local-dir="
                f"{self.model_dir}) — see tts/README.md."
            )

        logger.info(
            "loading_indextts2",
            device=self.device,
            fp16=self.use_fp16,
            cuda_kernel=self.use_cuda_kernel,
            model_dir=str(self.model_dir),
        )
        # Base kwargs match the documented IndexTTS-2 constructor
        # (cfg_path, model_dir, use_fp16, use_cuda_kernel, use_deepspeed).
        # VERIFY against the installed release — the API can drift.
        base_kwargs = dict(
            cfg_path=str(self.config_path),
            model_dir=str(self.model_dir),
            use_fp16=self.use_fp16,
            use_cuda_kernel=self.use_cuda_kernel,
            use_deepspeed=False,  # DeepSpeed off — not needed for a single 3060
        )
        try:
            # The README signature does NOT list `device`; some versions accept
            # it, others auto-select the GPU. Try WITH device first, then fall
            # back to the documented signature if that version rejects it.
            try:
                model = IndexTTS2(device=self.device, **base_kwargs)
            except TypeError:
                logger.warning("indextts2_no_device_kwarg", device=self.device,
                               note="constructor does not accept device=; using its default")
                model = IndexTTS2(**base_kwargs)
        except TypeError as exc:
            # Even the documented signature was rejected — make it obvious which
            # layer to fix rather than surfacing a bare TypeError to the client.
            raise TTSEngineError(
                f"IndexTTS2(...) rejected the constructor kwargs ({exc}). The "
                "IndexTTS2 API has likely changed — reconcile tts/engine.py "
                "_build_model() with the installed version."
            ) from exc
        except Exception as exc:  # pragma: no cover - depends on host/model
            raise TTSEngineError(f"Failed to load IndexTTS2: {exc}") from exc

        logger.info("indextts2_loaded")
        return model

    def load(self) -> None:
        """Build the model now if it is not already loaded (idempotent).

        Optional warm-up hook — synthesize() calls this itself. Guarded so two
        concurrent first-requests cannot build the model twice.
        """
        if self._model is not None:
            return
        self._ensure_reference_audio()
        with self._load_lock:
            if self._model is None:  # re-check inside the lock
                self._model = self._build_model()

    # -- synthesis ---------------------------------------------------------

    def _infer_to_file(self, text: str, out_path: Path, emo_vector: Optional[List[float]]) -> None:
        """Run one IndexTTS2 inference, writing a WAV to out_path.

        Caller holds self._lock. IndexTTS2.infer writes a file; we hand it a
        temp path and read the bytes back (it has no in-memory return), then
        re-wrap to a clean in-memory WAV in synthesize().
        """
        kwargs = dict(
            spk_audio_prompt=str(self.reference_audio),
            text=text,
            output_path=str(out_path),
            max_text_tokens_per_segment=self.max_text_tokens_per_segment,
            verbose=False,
        )
        # Only pass an explicit emotion vector when one was supplied; otherwise
        # let IndexTTS2 fall back to its neutral default (deriving emotion from
        # the speaker prompt). emo_alpha follows the documented API.
        if emo_vector is not None:
            kwargs["emo_vector"] = emo_vector
            kwargs["emo_alpha"] = 1.0

        try:
            self._model.infer(**kwargs)
        except TypeError as exc:
            raise TTSEngineError(
                f"IndexTTS2.infer(...) rejected its arguments ({exc}). The "
                "IndexTTS2 API has likely changed — reconcile tts/engine.py "
                "_infer_to_file() with the installed version."
            ) from exc
        except Exception as exc:  # pragma: no cover - depends on host/model
            raise TTSEngineError(f"IndexTTS2 synthesis failed: {exc}") from exc

    @staticmethod
    def _repackage_wav(path: Path) -> bytes:
        """Read the model's output WAV and re-emit clean canonical WAV bytes.

        Reading through the wave module (rather than returning the raw file)
        guarantees we hand back a well-formed RIFF/WAVE stream regardless of any
        extra chunks the model writer may add.
        """
        with wave.open(str(path), "rb") as wf:
            params = wf.getparams()
            frames = wf.readframes(wf.getnframes())
        buf = io.BytesIO()
        with wave.open(buf, "wb") as out:
            out.setparams(params)
            out.writeframes(frames)
        return buf.getvalue()

    def synthesize(self, text: str, emo_vector: Optional[Sequence[float]] = None) -> bytes:
        """Synthesize *text* to WAV bytes (the only public synth entry point).

        Validates input, lazily loads the model on first use, runs ONE inference
        under the instance lock, and returns in-memory WAV bytes. Never plays
        audio. Raises TTSEngineError (caller-facing) on any failure.
        """
        if not isinstance(text, str) or not text.strip():
            raise TTSEngineError("text must be a non-empty string")

        emo = validate_emo_vector(emo_vector)

        # Lazy load (also validates the reference clip) before taking the heavy
        # inference lock so a missing model/ref fails fast and clearly.
        self.load()

        # Serialise inference: IndexTTS2 is single-stream / not concurrency-safe.
        import tempfile

        with self._lock:
            with tempfile.TemporaryDirectory(prefix="vivi_tts_") as tmp:
                out_path = Path(tmp) / "out.wav"
                self._infer_to_file(text, out_path, emo)
                if not out_path.is_file():
                    raise TTSEngineError("synthesis produced no output file")
                return self._repackage_wav(out_path)
