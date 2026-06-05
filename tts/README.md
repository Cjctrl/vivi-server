# V.I.V.I Distributed TTS (IndexTTS2)

A tiny HTTP microservice that turns text into spoken **WAV bytes** using
[IndexTTS2](https://github.com/index-tts/index-tts) (GPU, autoregressive,
zero-shot, emotion-controllable). It runs on the **headless** memory box
(RTX 3060 12GB). The **brain** (`vivi-brain`, a separate machine) calls it over
HTTP, gets raw WAV bytes back, and streams them to clients itself
("brain-orchestrated").

> **Headless / return-only.** This box has no speakers. The service ONLY returns
> audio bytes — it never plays sound locally. There is no `simpleaudio` /
> `sounddevice` / `winsound` playback anywhere in `tts/`.

The `tts/` package is **import-safe without torch/indextts**: `torch` and
`indextts` are imported *inside* the synth call, so `import tts.server` works on
a box without the GPU stack (CI, the brain, a dev laptop). The model is
**lazy-loaded on the first `/tts` request**.

---

## HTTP contract

### `POST /tts`
```
Headers: Authorization: Bearer {TTS_SECRET}
         Content-Type: application/json
Body:    {
           "text": "string",
           "emo_vector": [happy, angry, sad, afraid, disgusted, melancholic, surprised, calm] | null,
           "voice_id": "vivi",      // optional, default "vivi"
           "format": "wav"          // optional, only "wav" supported
         }
```
- **200** → `Content-Type: audio/wav`, body = raw WAV bytes.
- **4xx/5xx** → `application/json` `{"error": "..."}`.

`emo_vector` is 8 floats, each `0.0–1.4`, **sum ≤ 0.8**; `null` ⇒ neutral
default. Bad length / range / sum ⇒ **400**.

### `GET /health` (no auth)
```json
{ "status": "ok", "model_loaded": false, "voices": ["vivi"] }
```
`model_loaded` flips to `true` after the first successful synth (lazy load).

### Auth
Bearer-only, **required on `/tts`** (`/health` stays open). The token is compared
with `hmac.compare_digest` (timing-safe). `TTS_SECRET` falls back to
`NEXUS_SECRET` when unset, so one deployment secret can cover both surfaces.

### Quick test
```bash
# Health (no auth):
curl -s http://127.0.0.1:7600/health

# Synthesize (neutral) -> out.wav:
curl -s -X POST http://127.0.0.1:7600/tts \
  -H "Authorization: Bearer $TTS_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"text":"Hello, this is Vivi.","emo_vector":null,"format":"wav"}' \
  --output out.wav

# Synthesize with a touch of "happy" (index 0); note sum must stay <= 0.8:
curl -s -X POST http://127.0.0.1:7600/tts \
  -H "Authorization: Bearer $TTS_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"text":"Good morning!","emo_vector":[0.6,0,0,0,0,0,0,0.2],"format":"wav"}' \
  --output happy.wav
```

---

## Install (Ubuntu, RTX 3060)

IndexTTS2 is installed from **its own checkout** with its own `uv`-managed venv.
Do **not** add torch/indextts to the shared `/opt/vivi/venv` — keep the heavy
stack isolated in the IndexTTS2 checkout.

```bash
# 1. Clone IndexTTS2
git clone https://github.com/index-tts/index-tts.git
cd index-tts

# 2. Git LFS (pulls the small in-repo assets)
git lfs install
git lfs pull

# 3. uv + dependencies (uv is the ONLY supported installer for IndexTTS2)
pip install -U uv
uv sync --all-extras

# 4. PyTorch — CUDA 12.1 build for Ampere (RTX 3060).
#    Use cu121 (Ampere), NOT the cu128/Blackwell wheels.
uv pip install torch torchvision torchaudio \
  --index-url https://download.pytorch.org/whl/cu121

# 5. Download model checkpoints (~weights into ./checkpoints)
uv tool install "huggingface-hub[cli,hf_xet]"
hf download IndexTeam/IndexTTS-2 --local-dir=checkpoints

# 6. Reference voice — a 5-15s CLEAN, mono WAV of the target voice.
#    The path must match VIVI_VOICE_REF (see config/settings.py).
mkdir -p reference_audio
#   ...copy your clip to reference_audio/vivi_voice.wav...
```

> **Default checkpoint layout.** The engine expects `checkpoints/config.yaml` and
> the weights under `checkpoints/` (override with the `model_dir` / `config_path`
> args in `tts/engine.py` if you relocate them).

### Make the `tts/` package importable
The service code lives in **vivi-server**, but runs from the **index-tts**
checkout (whose venv has torch). Put vivi-server on `PYTHONPATH`:

```bash
export PYTHONPATH=/opt/vivi/vivi-server:/opt/vivi/index-tts
export WS_SECRET=...      # required by config.settings (any value; unused by TTS)
export NEXUS_SECRET=...   # required by config.settings; TTS_SECRET falls back to it
export TTS_ENABLED=true
export TTS_HOST=127.0.0.1 # or this box's Tailscale IP when the brain is remote
export VIVI_VOICE_REF=/opt/vivi/vivi-server/reference_audio/vivi_voice.wav

# Run (from the index-tts checkout, using its venv python):
/opt/vivi/index-tts/.venv/bin/python -m tts.server
# (equivalently: python -m tts)
```

Then `curl http://127.0.0.1:7600/health` should return
`{"status":"ok","model_loaded":false,"voices":["vivi"]}`.

---

## systemd

Unit: [`deploy/vivi-tts.service`](../deploy/vivi-tts.service).

```bash
sudo cp deploy/vivi-tts.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now vivi-tts.service
journalctl -u vivi-tts.service -f
```

The unit runs from `/opt/vivi/index-tts` with
`PYTHONPATH=/opt/vivi/vivi-server:/opt/vivi/index-tts`, reads secrets from
`/etc/vivi/vivi.env`, and grants the NVIDIA device nodes (needed for CUDA under
`ProtectSystem=strict`). Adjust paths if your checkout lives elsewhere.

---

## VRAM budget (Scenario C — 12GB RTX 3060)

This card keeps its **memory** role AND runs IndexTTS2 warm. To make room, the
summarizer was dropped from `qwen3:14b` to `qwen3:8b` (see
`config/settings.py`, MODELS / Scenario C).

| Component            | VRAM    | Notes                                            |
|----------------------|---------|--------------------------------------------------|
| nomic-embed-text     | ~0.6 GB | every Qdrant vector op (unchanged)               |
| IndexTTS2 (FP16)     | ~4.5 GB | warm, single-stream (`tts/engine.py`)            |
| qwen3:8b-q4          | ~4.0 GB | summarizer — **down from qwen3:14b-q4 (~9 GB)**  |
| CUDA / context       | ~0.7 GB | driver + kernels                                 |
| **Total**            | **~9.8 GB used** | → **~2.2 GB free** on a 12GB 3060       |

Pin the resident Ollama tier so it can't collide with the warm TTS process:
`OLLAMA_KEEP_ALIVE=-1`, `OLLAMA_MAX_LOADED_MODELS=2`, `OLLAMA_NUM_PARALLEL=1`
(see `deploy/systemd/ollama.service.d/override.conf`).

To put the 14B summarizer back, run TTS on a **separate** GPU
(`TTS_ENABLED=false` here) — Scenario C's whole point is memory + TTS on one card.

---

## Configuration (`config/settings.py`)

| Setting          | Default                                   | Meaning                                                        |
|------------------|-------------------------------------------|----------------------------------------------------------------|
| `TTS_ENABLED`    | `False`                                   | Master switch (intent/wiring; import is safe regardless).      |
| `TTS_HOST`       | `NEXUS_HOST` (`127.0.0.1`)                | Bind address; set to the Tailscale IP for remote brain access. |
| `TTS_PORT`       | `7600`                                    | Listen port.                                                   |
| `TTS_SECRET`     | `NEXUS_SECRET` (fallback)                 | Bearer token gating `/tts`. Never hardcoded.                   |
| `TTS_DEVICE`     | `cuda:0`                                  | torch device handed to IndexTTS2.                              |
| `VIVI_VOICE_REF` | `<repo>/reference_audio/vivi_voice.wav`   | 5–15s clean ref clip cloned for synthesis.                     |

---

## ⚠️ Verify against the installed IndexTTS2 release

The IndexTTS2 Python API can drift between versions. The kwargs used in
`tts/engine.py` reflect the documented IndexTTS-2 API at the time of writing —
**re-check them against the version you actually installed**:

- **Constructor** `IndexTTS2(cfg_path=, model_dir=, use_fp16=, use_cuda_kernel=,
  use_deepspeed=, [device=])`. The documented signature does **not** list
  `device`; the engine tries `device=` first and falls back to the documented
  signature if that version rejects it. `use_cuda_kernel=True` requires the
  compiled CUDA kernel to build — if it fails, set it `False`.
- **Inference** `infer(spk_audio_prompt=, text=, output_path=, emo_vector=,
  emo_alpha=, max_text_tokens_per_segment=, verbose=)`. The engine passes
  `emo_vector` + `emo_alpha=1.0` only when an emotion vector is supplied
  (otherwise neutral). `max_text_tokens_per_segment=80` keeps peak VRAM down.

If a kwarg is rejected, reconcile `tts/engine.py` (`_build_model()` /
`_infer_to_file()`) with the installed release — the public `synthesize()` /
HTTP interface stays the same.
