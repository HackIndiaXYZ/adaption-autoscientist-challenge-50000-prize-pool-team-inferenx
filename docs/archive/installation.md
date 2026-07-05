# CineLocalAI — CPU-Only Installation Guide
**Target: Windows 11 · Python 3.11 · No NVIDIA GPU**

---

## Hardware Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | Any quad-core | Intel i5/i7 or AMD Ryzen 5/7 (8th gen+) |
| RAM | 8 GB | **16 GB** |
| Disk | 6 GB free | 10 GB free |
| GPU | **Not required** | N/A |
| OS | Windows 10 | **Windows 11** |

> **RAM note:** Whisper `base` uses ~1.5 GB. The full pipeline peak RAM is ~4–6 GB.
> 8 GB is tight but workable. 16 GB recommended for comfort.

---

## Step 1 — Verify Python 3.11

```powershell
python --version
# Must show: Python 3.11.x
```

If not installed, download from https://www.python.org/downloads/release/python-3119/

> ⚠ **Do NOT use Python 3.12** — Coqui TTS 0.22 is incompatible.

---

## Step 2 — Install FFmpeg

FFmpeg is required for the final video composition stage.

```powershell
# Option A — winget (built into Windows 11, easiest)
winget install ffmpeg

# Option B — Chocolatey
choco install ffmpeg
```

Verify:
```powershell
ffmpeg -version
# Should print: ffmpeg version 6.x ...
```

If FFmpeg is not on your PATH after install, restart your terminal or add it manually:
- Default winget install path: `C:\Users\<you>\AppData\Local\Microsoft\WinGet\Packages\...`
- Or download a static build from https://www.gyan.dev/ffmpeg/builds/ and add `bin\` to your PATH.

---

## Step 3 — Create Virtual Environment

```powershell
cd "c:\Users\konne balraju\OneDrive\Desktop\AI Auto Scientis HACKATHON\cinelocalai"

python -m venv venv
venv\Scripts\activate
```

Your prompt should show `(venv)` after activation.

---

## Step 4 — Install PyTorch (CPU Build)

> Must be installed **before** `requirements.txt` — Coqui TTS pins `torch<2.1`.

```powershell
pip install torch==2.0.1 torchvision==0.15.2 torchaudio==2.0.2
```

This downloads ~800 MB of CPU-only PyTorch wheels.

Verify:
```powershell
python -c "import torch; print(torch.__version__); print('CUDA:', torch.cuda.is_available())"
# Expected: 2.0.1   CUDA: False
```

---

## Step 5 — Install All Other Dependencies

```powershell
pip install -r requirements.txt
```

This installs (in addition to PyTorch):

| Package | Purpose | Size |
|---------|---------|------|
| `openai-whisper` | Speech-to-text transcription | ~10 MB |
| `transformers` | Emotion tagger + MarianMT translation | ~6 MB |
| `sentencepiece` | MarianMT tokenizer | ~2 MB |
| `sacremoses` | MarianMT Hindi pre-processing | ~1 MB |
| `accelerate` | Transformers device management | ~1 MB |
| `TTS==0.22.0` | Coqui TTS speech synthesis | ~5 MB |
| `pydub`, `soundfile` | Audio merging | ~2 MB |
| `PyYAML`, `tqdm`, `numpy` | Config / utilities | ~20 MB |

---

## Step 6 — Verify All Packages

```powershell
python -c "import whisper; print('Whisper OK')"
python -c "from transformers import MarianMTModel; print('Transformers OK')"
python -c "from TTS.api import TTS; print('Coqui TTS OK')"
python -c "from pydub import AudioSegment; print('pydub OK')"
python -c "import yaml; print('PyYAML OK')"
```

All five should print `OK`. If any fail, re-run `pip install -r requirements.txt`.

---

## Step 7 — First Run

Place a short (5–30s) English `.mp4` video in the `demo/` folder, then:

```powershell
python main.py --input demo\sample.mp4 --log-level INFO
```

Models are downloaded automatically on first run. Expect ~10 minutes of downloads
before the pipeline itself starts.

---

## Model Download Sizes (First Run Only)

| Model | Download Size | Stage |
|-------|--------------|-------|
| Whisper `base` | 145 MB | Stage 1 — Transcription |
| DistilRoBERTa emotion | 330 MB | Stage 2 — Emotion Tagging |
| MarianMT `en→hi` | 300 MB | Stage 3 — Translation |
| Hindi VITS (TTS fallback) | 60 MB | Stage 4 — Speech synthesis |
| **Total first-run** | **~835 MB** | |

> XTTS v2 (~1.8 GB) is **not downloaded** unless you set `speaker_wav` in the config.

---

## CPU Runtime Estimates (10-second English video)

| Stage | Model Used | Estimated Time |
|-------|-----------|----------------|
| Stage 1 — Transcription | Whisper `base` | 20–40 seconds |
| Stage 2 — Emotion Tagging | DistilRoBERTa | 5–15 seconds |
| Stage 3 — Translation | MarianMT en→hi | 5–15 seconds |
| Stage 4 — TTS (fallback) | Hindi VITS | 30–90 seconds |
| Stage 5 — Composition | FFmpeg | 3–8 seconds |
| **Total** | | **~1 – 3 minutes** |

> If you switch to `--whisper small`: Stage 1 takes 60–90s but accuracy improves.  
> If you enable XTTS v2 with `speaker_wav`: Stage 4 takes **5–15 min per segment** — not recommended for CPU MVP testing.

---

## Whisper Model Comparison (CPU)

| Model | Size | 10s video time | Accuracy |
|-------|------|---------------|----------|
| `tiny` | 39 MB | ~10s | Low |
| **`base`** ← default | 145 MB | ~20-40s | **Good** |
| `small` | 460 MB | ~60-90s | Better |
| `medium` | 1.5 GB | ~8-15 min | High (not for MVP) |
| `large` | 3 GB | ~20-40 min | Highest (not for CPU) |

Change the model in `config/settings.yaml`:
```yaml
whisper_model: "base"   # or "small" for better accuracy
```

---

## TTS Mode Comparison (CPU)

| Mode | Config | 10s video time | Voice quality |
|------|--------|---------------|---------------|
| **Hindi VITS (fallback)** ← default | `speaker_wav: null` | 30–90s | Robotic but functional |
| XTTS v2 | `speaker_wav: path/to/ref.wav` | 5–15 min/segment | Natural voice clone |

**For CPU MVP: keep `speaker_wav: null`** (Hindi VITS fallback, no reference audio needed).

---

## Disk Space Summary

| Component | Size |
|-----------|------|
| Python venv + packages | ~4.0 GB |
| Downloaded models (first run) | ~835 MB |
| Per pipeline run output (10s video) | ~30 MB |
| **Total** | **~5 GB** |

---

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `ffmpeg: command not found` | Run `winget install ffmpeg`, then open a new terminal |
| `ERROR installing TTS` due to torch conflict | Ensure you installed `torch==2.0.1` BEFORE running `pip install -r requirements.txt` |
| `ModuleNotFoundError: sacremoses` | `pip install sacremoses>=0.0.53` |
| `Transcription returned 0 segments` | Video has no speech or wrong `src_lang`. Check the audio with a media player. |
| Stage 4 taking very long | You may have accidentally set `speaker_wav` — set it back to `null` to use fast VITS fallback |
| Out of memory during TTS | Close other applications. Whisper `base` + VITS uses ~3-4 GB RAM total. |
| `numpy` version error | `pip install "numpy>=1.24.0,<2.0"` |
