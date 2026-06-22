"""
tts/tune.py
Offline voice-tuning bench for the V.I.V.I IndexTTS2 service.

Run this ON the server box (the one with the GPU + checkpoints + reference clip)
to dial in the voice BY EAR before flipping TTS_ENABLED on. It renders a small
sweep of {emotion preset} x {emo_alpha} x {sample line} to labeled WAV files you
can listen to back-to-back, then you copy the winning values into .env:

    TTS_EMO_ALPHA=0.65
    TTS_INTERVAL_SILENCE_MS=200
    TTS_MAX_TOKENS_PER_SEGMENT=80

It reuses the real ViviTTS engine, so what you hear is exactly what the service
produces. The model loads once and stays warm across the whole sweep.

Usage (from the vivi-server repo root, in the venv that has torch/indextts):
    python -m tts.tune                          # default small sweep
    python -m tts.tune --alphas 0.4,0.6,0.8     # sweep emo_alpha only
    python -m tts.tune --emotions happy,curious,concerned
    python -m tts.tune --text "Good morning, sir." --alphas 0.5,0.7
    python -m tts.tune --out tts/tune_out --voice reference_audio/vivi_voice.wav
    python -m tts.tune --list                   # list preset names (no GPU needed)

Requires WS_SECRET / NEXUS_SECRET in the environment (config.settings reads them);
they are imported lazily so --list / --help work without them.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Preset 8-D emotion vectors [happy, angry, sad, afraid, disgusted, melancholic,
# surprised, calm]; each component 0..1.4, the whole vector sums to <= 0.8. These
# are fixed *test fixtures* for the ear-test only — the live service derives its
# vector continuously from the brain's emotion engine, but stable presets give you
# clean A/B reference points. "default" passes NO vector (the model's own neutral,
# your baseline); "neutral" nudges calm-dominant.
PRESETS: "dict[str, list[float] | None]" = {
    "default":     None,
    "neutral":     [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.4],
    "happy":       [0.6, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2],
    "excited":     [0.5, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.0],
    "curious":     [0.2, 0.0, 0.0, 0.0, 0.0, 0.0, 0.2, 0.2],
    "serious":     [0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.0, 0.5],
    "sympathetic": [0.1, 0.0, 0.2, 0.0, 0.0, 0.2, 0.0, 0.1],
    "playful":     [0.4, 0.0, 0.0, 0.0, 0.0, 0.0, 0.3, 0.0],
    "concerned":   [0.0, 0.0, 0.2, 0.2, 0.0, 0.1, 0.0, 0.1],
}

DEFAULT_LINES = [
    "Good morning, sir. All systems are operational.",
    "I found the issue — it was on line forty-two.",
    "I'm not certain that's wise, but I'll proceed.",
]

DEFAULT_EMOTIONS = ["neutral", "happy", "curious", "concerned"]
DEFAULT_ALPHAS = [0.45, 0.65, 0.85]


def _slug(text: str, n: int = 24) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return s[:n] or "line"


def _build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="IndexTTS2 voice-tuning bench for V.I.V.I")
    ap.add_argument("--out", default="tts/tune_out", help="output directory for WAVs")
    ap.add_argument("--emotions", default=",".join(DEFAULT_EMOTIONS),
                    help="comma list of preset names (see --list)")
    ap.add_argument("--alphas", default=",".join(str(a) for a in DEFAULT_ALPHAS),
                    help="comma list of emo_alpha values (0..1)")
    ap.add_argument("--text", default=None,
                    help="a single line to render (overrides the default sample set)")
    ap.add_argument("--lines", type=int, default=1,
                    help=f"how many default sample lines to use (1..{len(DEFAULT_LINES)})")
    ap.add_argument("--voice", default=None, help="reference voice WAV (default: VIVI_VOICE_REF)")
    ap.add_argument("--device", default=None, help="torch device (default: TTS_DEVICE)")
    ap.add_argument("--max-tokens", type=int, default=None,
                    help="max_text_tokens_per_segment override")
    ap.add_argument("--interval-silence", type=int, default=None,
                    help="interval_silence ms override")
    ap.add_argument("--list", action="store_true", help="list preset names and exit")
    return ap


def main(argv: "list[str] | None" = None) -> int:
    args = _build_parser().parse_args(argv)

    if args.list:
        print("Presets:", ", ".join(PRESETS))
        return 0

    # Imported HERE so --list / --help need neither torch nor the config secrets.
    from config.settings import (
        TTS_DEVICE,
        TTS_EMO_ALPHA,
        TTS_INTERVAL_SILENCE_MS,
        TTS_MAX_TOKENS_PER_SEGMENT,
        VIVI_VOICE_REF,
    )
    from tts.engine import TTSEngineError, ViviTTS

    emotions = [e.strip() for e in args.emotions.split(",") if e.strip()]
    unknown = [e for e in emotions if e not in PRESETS]
    if unknown:
        print(f"Unknown preset(s): {unknown}. Known: {', '.join(PRESETS)}", file=sys.stderr)
        return 2
    try:
        alphas = [float(a) for a in args.alphas.split(",") if a.strip() != ""]
    except ValueError:
        print("--alphas must be a comma list of numbers, e.g. 0.4,0.6,0.8", file=sys.stderr)
        return 2
    if not emotions or not alphas:
        print("Nothing to render — provide at least one --emotions and one --alphas value.",
              file=sys.stderr)
        return 2

    if args.text:
        lines = [args.text]
    else:
        n = max(1, min(args.lines, len(DEFAULT_LINES)))
        lines = DEFAULT_LINES[:n]

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)

    engine = ViviTTS(
        reference_audio=args.voice or VIVI_VOICE_REF,
        device=args.device or TTS_DEVICE,
        use_fp16=True,
        use_cuda_kernel=True,
        max_text_tokens_per_segment=args.max_tokens or TTS_MAX_TOKENS_PER_SEGMENT,
        emo_alpha=TTS_EMO_ALPHA,
        interval_silence_ms=(args.interval_silence
                             if args.interval_silence is not None
                             else TTS_INTERVAL_SILENCE_MS),
        voice_id="vivi",
    )

    combos = [(li, line, emo, a)
              for li, line in enumerate(lines)
              for emo in emotions
              for a in alphas]
    print(f"Rendering {len(combos)} clip(s) to {out_dir.resolve()} "
          f"(voice={engine.reference_audio.name}, device={engine.device})\n")

    rows = []
    for idx, (li, line, emo, a) in enumerate(combos, start=1):
        vec = PRESETS[emo]
        name = f"{idx:02d}_{emo}_a{a:.2f}_L{li + 1}_{_slug(line)}.wav"
        path = out_dir / name
        try:
            wav = engine.synthesize(line, emo_vector=vec, emo_alpha=a)
            path.write_bytes(wav)
            status = f"OK {len(wav)} bytes"
        except TTSEngineError as exc:
            status = f"FAIL {exc}"
        except Exception as exc:  # keep the sweep going on a single bad render
            status = f"ERROR {exc}"
        print(f"[{idx:02d}/{len(combos)}] {emo:<12} a={a:<5} L{li + 1}  -> {name}  {status}")
        rows.append(f"{name}\temo={emo}\talpha={a}\tline={line!r}\t{status}")

    manifest = out_dir / "MANIFEST.txt"
    manifest.write_text("\n".join(rows) + "\n", encoding="utf-8")
    print(f"\nManifest: {manifest}")
    print("Listen, pick the alpha/emotion that sounds right, then set TTS_EMO_ALPHA "
          "(and TTS_INTERVAL_SILENCE_MS / TTS_MAX_TOKENS_PER_SEGMENT) in .env.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
