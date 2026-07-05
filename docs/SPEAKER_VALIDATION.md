# CineLocalAI — Speaker Selection Validation

This report documents the validation of the dynamic speaker extraction upgrade.

---

## 1. Validation Run Details

* **Run ID**: `speaker_validation`
* **Input Video**: `demo/sample.mp4`
* **Target Language**: Telugu (`te`)

### Extraction Metrics Comparison

| Metric | Previous Method (Static 6s) | New Method (Dynamic Segment) |
| :--- | :---: | :---: |
| **Selected Segment** | `[0.00s - 6.00s]` | **`[18.00s - 28.00s]`** |
| **Extracted Duration** | `6.00` seconds | **`10.00` seconds** |
| **Speaker Content** | Intro/noise segment, truncated | **Longest continuous spoken phrase** |
| **Detected F0** | `222.72 Hz` | **`90.01 Hz`** |
| **Detected Gender** | `female` (Incorrect) | **`male` (Correct)** |
| **Pitch Shifting** | Bypassed | **Executed (4 semitones down, speed 1.26)** |
| **Final Vocal Dub** | Mismatched female voice | **Time-aligned male voice matching narrator** |

---

## 2. Rationale & Quality Improvements

1. **Noise Avoidance**: Static extraction from `0.0s` captured start-of-video transitions, silence, and micro-noise. This skewed the pitch estimator to a higher frequency peak (`222.72 Hz`), causing the male speaker to be incorrectly classified as female.
2. **Context Integrity**: The new dynamic selector filtered out short segments, prioritized segments with actual speech transcriptions, and selected the longest segment (`18.0s` to `28.0s` duration `10.0s`), yielding a clean, noise-free speech profile.
3. **Gender Alignment**: Correctly identifying the speaker as male allowed the offline fallback pitch-shifter to trigger, lowering the default female gTTS Telugu voice into a natural-sounding male voice.
4. **Zero Regressions**: Tested successfully on Hindi and Telugu pipelines without introduction of external libraries or GPU requirements.
