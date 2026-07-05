# CineLocalAI — Architecture Documentation

This document describes the offline video dubbing pipeline architecture and the localization model routing layer.

---

## 1. System Overview

CineLocalAI coordinates several offline deep learning models sequentially to translate, tag, synthesize, and dub movie clips and video segments.

All operations run locally without requiring cloud dependencies or API keys.

---

## 2. Current Production Pipeline

The current pipeline runs sequentially using the standard Seq2Seq NLLB-200 translation model.

```
+--------------------+
| Input Video/Audio  |
+---------+----------+
          |
          v
+--------------------+
| 1. Whisper ASR     |  --> Transcribes audio/video to timestamped text segments
+---------+----------+
          |
          v
+--------------------+
| 2. Emotion Tagger  |  --> j-hartmann/emotion-english-distilroberta-base labels per segment
+---------+----------+
          |
          v
+--------------------+
| 3. NLLB-200        |  --> Offline translation to target language (Hindi, Telugu, etc.)
+---------+----------+
          |
          v
+--------------------+
| 4. TTS Synthesis   |  --> Coqui XTTS v2 / VITSfallback synthesizes emotion-aware speech
+---------+----------+
          |
          v
+--------------------+
| 5. Video Composer  |  --> FFmpeg + pydub merges original background, dubbed audio & subtitles
+---------+----------+
          |
          v
+--------------------+
| Output Dubbed MP4  |
+--------------------+
```

---

## 3. Future Enhanced Pipeline

For architecture readiness, a dynamic `ModelRouter` has been integrated. This layer allows seamless backend selection between standard NLLB-200 and the PEFT LoRA adapter for `Mixtral-8x7B-Instruct-v0.1` via simple settings or runtime routing.

```
+--------------------+
| Input Video/Audio  |
+---------+----------+
          |
          v
+--------------------+
| 1. Whisper ASR     |
+---------+----------+
          |
          v
+--------------------+
| 2. Emotion Tagger  |
+---------+----------+
          |
          v
+--------------------+
| 3. Model Router    |  ==================================+
+---------+----------+                                    |
          |                                               |
          +------------------+                            |
          |                  |                            |
          v                  v                            v
   +--------------+   +--------------+             +--------------+
   |   NLLB-200   |   | Mixtral-8x7B |             | Auto Routing |
   |  (Seq2Seq)   |   |   + LoRA     |             | (Dynamic)    |
   +------+-------+   +------+-------+             +------+-------+
          |                  |                            |
          +------------------+----------------------------+
          |
          v
+--------------------+
| 4. TTS Synthesis   |
+---------+----------+
          |
          v
+--------------------+
| 5. Video Composer  |
+---------+----------+
          |
          v
+--------------------+
| Output Dubbed MP4  |
+--------------------+
```

---

## 4. Backend Routing Configurations

Backend switching is controlled via `config/settings.yaml`:

```yaml
localization:
  backend: "nllb"  # Allowed backends: 'nllb', 'lora', 'auto'

models:
  lora_path: "models/adaption_mixtral_lora"
  base_model: "mistralai/Mixtral-8x7B-Instruct-v0.1"
```

### Routing Modes

1. **`nllb` (Default)**: Directly routes all queries to the local `facebook/nllb-200-distilled-600M` model. Fast, lightweight, and CPU-friendly.
2. **`lora` (Compatibility / Test Mode)**: Routes translation to the optional `LocalizationModel` wrapper. Due to resource constraints on typical local devices, running the 46B parameter base model is bypassed; a warning is logged and translation safely falls back to NLLB to maintain end-to-end functionality.
3. **`auto`**: Dynamically checks if the LoRA adapter is present. If it is available, it switches to compatibility mode; otherwise, it resolves to NLLB.
