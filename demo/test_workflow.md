# CineLocalAI — Test Workflow Guide

## Overview

This guide walks you through running the CineLocalAI MVP pipeline end-to-end
on a short English video to produce a Hindi dubbed output.

---

## Prerequisites

Before running, confirm all dependencies are installed:

```bash
python --version          # Must be 3.9–3.11
ffmpeg -version           # Must be on PATH
pip show openai-whisper   # Whisper installed?
pip show TTS              # Coqui TTS installed?
```

See `installation.md` for full setup instructions.

---

## Step 1 — Prepare Your Test Video

Place a short (5–30 second) English `.mp4` file in the `demo/` folder:

```
cinelocalai/
└── demo/
    └── sample.mp4     ← your test video goes here
```

> **Requirements for the test video:**
> - Must contain **audible English speech**
> - Must have an **audio track** (not a silent video)
> - Recommended length: 5–30 seconds for first test
> - Any resolution/codec is fine (FFmpeg handles conversion)

---

## Step 2 — Run the Pipeline

### Option A — Using the Demo Script (simplest)

```bash
cd cinelocalai
python demo/run_demo.py
```

### Option B — Using the CLI

```bash
cd cinelocalai

# English → Hindi (default)
python main.py --input demo/sample.mp4

# English → French
python main.py --input demo/sample.mp4 --tgt fr

# Use larger Whisper for better accuracy
python main.py --input demo/sample.mp4 --whisper small

# Enable debug logging
python main.py --input demo/sample.mp4 --log-level DEBUG
```

### Option C — Voice Cloning (XTTS v2, optional)

```bash
# Provide a 6–30s .wav reference speaker audio for voice cloning
python main.py --input demo/sample.mp4 --speaker-wav demo/my_voice.wav
```

---

## Step 3 — Expected Pipeline Output

The pipeline runs in 5 stages. You will see logs like:

```
[Pipeline] Stage 1/5 → Transcription
[TranscriptAgent] Transcribing: demo/sample.mp4
[TranscriptAgent] Done | lang=en | segments=8

[Pipeline] Stage 2/5 → Emotion Tagging
[EmotionTagger] Tagging 8 segments...

[Pipeline] Stage 3/5 → Translation
[TranslationAgent] Translating 8 segments (batch=8)...

[Pipeline] Stage 4/5 → TTS Synthesis
[TTSAgent] FALLBACK mode | model: tts_models/hi/cv/vits
[TTSAgent] Synthesizing 8 segments...

[Pipeline] Stage 5/5 → Video Composition
[ComposerAgent] Composing final video...
```

---

## Step 4 — Expected Output Files

After a successful run:

```
cinelocalai/
├── data/
│   ├── transcripts/
│   │   └── demo_run_001_transcript.json   ← raw Whisper output
│   └── checkpoints/demo_run_001/
│       ├── transcript.json
│       ├── emotion_tagged.json
│       ├── translated.json
│       ├── synthesized.json
│       ├── merged_dubbed.wav              ← combined TTS audio
│       └── subtitles.srt                 ← generated subtitles
└── outputs/
    ├── tts/
    │   ├── segment_0000.wav
    │   ├── segment_0001.wav
    │   └── ...
    └── final/
        ├── demo_run_001_dubbed.mp4        ← ✓ FINAL OUTPUT
        └── demo_run_001_metadata.json
```

---

## Step 5 — Verify the Output

```bash
# Play the dubbed video (Windows)
start outputs/final/demo_run_001_dubbed.mp4

# Check metadata
type outputs\final\demo_run_001_metadata.json
```

---

## Troubleshooting

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FFmpeg not found` | FFmpeg not on PATH | Install FFmpeg — see `installation.md` |
| `Transcription returned 0 segments` | Silent video or wrong language | Ensure video has speech; check `src_lang` in config |
| `ImportError: sacremoses` | Missing dependency | `pip install sacremoses` |
| `No fallback model for language 'te'` | Coqui TTS has no single-speaker Telugu fallback | Provide a `speaker_wav` for Telugu XTTS v2 voice cloning, otherwise it will fallback to English TTS |
| Model downloads taking long | First-time downloads | Whisper base ~145 MB, Hindi VITS ~60 MB |
| TTS output sounds robotic | Fallback mode limitation | Provide a `speaker_wav` for XTTS v2 voice cloning |
| `JSONDecodeError` on resume | Corrupted checkpoint | Delete `data/checkpoints/<run_id>/` and re-run |

---

## Checkpoint / Resume

If the pipeline crashes mid-run, re-run the same command.
It will resume from the last completed stage automatically:

```bash
# Resume a specific run
python main.py --input demo/sample.mp4 --run-id demo_run_001
```

---

## Supported Language Pairs

| Source | Target | Code |
|--------|--------|------|
| English | Hindi | `--tgt hi` |
| English | Telugu | `--tgt te` |
| English | French | `--tgt fr` |
| English | German | `--tgt de` |
| English | Spanish | `--tgt es` |
| English | Italian | `--tgt it` |
| English | Chinese | `--tgt zh` |

---

## Estimated Run Times (CPU, 10-second video)

| Stage | Time |
|-------|------|
| Transcription (Whisper base) | ~20–60s |
| Emotion Tagging | ~10–30s |
| Translation (MarianMT) | ~5–15s |
| TTS (Hindi VITS fallback) | ~30–90s |
| Composition (FFmpeg) | ~5–10s |
| **Total** | **~2–4 minutes** |
