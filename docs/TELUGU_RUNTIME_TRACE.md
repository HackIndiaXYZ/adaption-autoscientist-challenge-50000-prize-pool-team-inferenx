# Telugu Synthesis Runtime Trace Report

This report presents a detailed runtime trace of the pipeline execution during the Telugu translation run `debug_telugu_trace` on `demo/sample.mp4`.

---

## 1. Trace Responses

### 1. Which TTS backend is used?
* **gTTS (Google Text-to-Speech)**. Because Telugu (`te`) is not supported by XTTS v2, and no native offline model is defined in `FALLBACK_MODELS` (VITS or Tacotron2), the pipeline routes synthesis to gTTS.

### 2. Whether `speaker_wav` is present?
* **No**. The command-line invocation did not provide an explicit `--speaker-wav` argument, so the pipeline initially started with `speaker_wav = None`.

### 3. Whether `extracted_speaker.wav` is actually passed into synthesis?
* **Yes**. In `pipeline.py`, the pipeline auto-extracted a 6-second audio clip from `demo/sample.mp4` to `data/checkpoints/debug_telugu_trace/extracted_speaker.wav`. The file path was set to `self.tts_agent.speaker_wav`.

### 4. Whether gender detection executes?
* **Yes**. In `pipeline.py`, `hasattr(self.tts_agent, "_estimate_gender")` evaluated to `True`, triggering the `_estimate_gender` method in `TTSAgent`.

### 5. What gender is detected?
* **`female`**. The autocorrelation fundamental frequency (F0) analysis of the auto-extracted audio clip (`extracted_speaker.wav`) computed a median frequency of **`222.72 Hz`**. Since this is well above the male threshold of `165 Hz`, the system classified the source speaker's voice as female.

### 6. Whether pitch shifting executes?
* **No**. Pitch-shifting is conditioned on a male speaker detection (`self.speaker_gender == "male"`) to convert the default female gTTS voice into a male voice. Since the detected gender was `female`, the pitch-shifting block was skipped.

### 7. Which audio file is modified?
* **No files were modified by pitch shifting** (since gender was female).
* **`outputs/tts/segment_0001.wav`** was modified by **emotion prosody post-processing** (its cinematic label was classified as `"tense"`, which triggered an offline speed of `0.95` and pitch offset of `-1`, resulting in an effective speed factor of `0.90`).

### 8. Whether the modified file is actually used by ComposerAgent?
* **Yes**. The `ComposerAgent` reads the segment clips directly from `outputs/tts/` to construct the timeline-aligned audio track.

### 9. The exact file path flow:

```
translated text (NLLB)
   ├─ Hindi: data/checkpoints/debug_telugu_trace/translated.json
   └─ Telugu: data/checkpoints/debug_telugu_trace/translated.json
        │
        v
generated audio file (gTTS)
   └─ outputs/tts/segment_0000.wav, segment_0001.wav, segment_0002.wav, segment_0003.wav
        │
        v
postprocessed audio file (pydub emotion adjustment)
   └─ outputs/tts/segment_0001.wav (overwritten in-place with emotion prosody)
        │
        v
composer input file (pydub overlay)
   └─ data/checkpoints/debug_telugu_trace/merged_dubbed.wav
        │
        v
final video (FFmpeg composition)
   └─ outputs/final/debug_telugu_trace_dubbed.mp4
```

### 10. Confirm whether the final composed audio comes from:
* **The emotion-postprocessed gTTS output**. The final composed audio track (`merged_dubbed.wav`) contains the in-place modified gTTS segments. The audio for segment 1 features emotional adjustments, while segments 0, 2, and 3 play standard female gTTS clips since the source voice in `demo/sample.mp4` is female.
