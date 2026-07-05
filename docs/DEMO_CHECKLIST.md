# CineLocalAI — Demo Checklist

This document verifies the readiness of the generated output videos and assets for judging demonstrations.

---

## 1. Demo Readiness Checklist

* **[x] Input Video Exists**: `demo/sample.mp4` is present (28 seconds, single-narrator English speech).
* **[x] Hindi Demo Videos**: 
  - `outputs/final/test_1_male_hi_dubbed.mp4` (Validated - cloned male voice).
  - `outputs/final/test_2_female_hi_dubbed.mp4` (Validated - cloned female voice).
* **[x] Telugu Demo Videos**: 
  - `outputs/final/test_3_male_te_dubbed.mp4` (Validated - pitch-shifted fallback male voice).
  - `outputs/final/test_4_female_te_dubbed.mp4` (Validated - default female gTTS voice).
* **[x] Subtitles Generated**: High-quality SRT files saved in each checkpoint folder (e.g. `data/checkpoints/test_3_male_te/subtitles.srt`).
* **[x] Audio Synchronization**: Dynamic time compression (speedup) executed successfully, adjusting lengths to prevent segment overlap and phrase truncation.
* **[x] Speaker Preservation**: Demonstrated via autocorrelation F0 estimation and DSP pitch-shifting on fallback paths.

---

## 2. Recommended Showcase Asset

### Target Demo: **`test_3_male_te_dubbed.mp4`**
* **Why this is the best showcase**: 
  - It demonstrates the **fallback DSP voice-preservation architecture**.
  - It shows the pipeline successfully bypassing XTTS constraints for Telugu, running local F0 classification on `speaker.wav` (90.01 Hz), identifying the gender as male, and pitch-shifting the default female gTTS output down by 4 semitones while restoring speed (1.26x).
  - It showcases **dynamic timing correction** aligning segments to the original timeline without truncation.
  - This illustrates how the team solved voice cloning and timing drift limitations in unsupported dialects without requiring heavy GPUs or cloud services.
