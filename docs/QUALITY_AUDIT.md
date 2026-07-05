# CineLocalAI — End-to-End Quality Audit

This document presents a comprehensive quality audit of the CineLocalAI pipeline stages, detailing how information is handled, what is lost, what is preserved, and the impact on final dubbing quality.

---

## 1. Stage-by-Stage Quality Audit

### Stage 1: TranscriptAgent (Whisper ASR)
* **Information Received**: Raw analog audio track extracted from the input video.
* **Information Lost**: 
  * Acoustic characteristics: Voice identity, gender cues, pitch, tone, speaking style, accent.
  * Expressive elements: Emotional intonation, non-verbal vocalizations (laughter, sighing, pauses).
* **Information Preserved**: Semantic text transcript and segment-level start/end timestamps.
* **Impact on Final Quality**: Establishes the temporal boundaries for all downstream stages. Loss of acoustic cues means speaker and emotion tags must be rebuilt from scratch semantically or via auxiliary analyses.

### Stage 2: EmotionTagger (DistilRoBERTa)
* **Information Received**: Semantic text segments.
* **Information Lost**: Acoustic-only emotional expressions (e.g., neutral text spoken with sarcasm, anger, or urgency).
* **Information Preserved**: Textual semantic emotion labels (Ekman 6 + neutral classification) and confidence scores.
* **Impact on Final Quality**: Guides translation style registers and configures speech synthesis speeds. The primary limitation is that it cannot tag emotion from audio cues directly.

### Stage 3: TranslationAgent (ModelRouter -> NLLB / LoRA)
* **Information Received**: English source text segments and emotion tags.
* **Information Lost**: Word-level timing alignments, language-specific idioms, and double-entendres.
* **Information Preserved**: Structural semantics, conceptual meaning, and register matching (formal vs. informal).
* **Impact on Final Quality**: Crucial for natural phrasing. English-to-Telugu translation introduces significant text expansion, causing timing conflicts where translated text requires more time to speak than the source segment.

### Stage 4: TTSAgent (XTTS v2 / Fallbacks)
* **Information Received**: Localized text segments, reference speaker audio files (`speaker_wav`), and emotion tags.
* **Information Lost**: 
  * Phoneme-level timing sync (does not match lip shapes).
  * In fallback/gTTS modes: Micro-prosody and speaking style of the original speaker are lost.
* **Information Preserved**: 
  * Synthesized voice naturalness.
  * Hindi: Cloned speaker identity (pitch, tone, gender) via XTTS.
  * Telugu/Fallbacks: Male/female characteristics via fundamental frequency (F0) profiling and DSP pitch-shifting.
* **Impact on Final Quality**: Directly generates the vocal dub. Timing adjustments and voice profiling prevent the voice from reverting to static, mismatched default genders.

### Stage 5: ComposerAgent (FFmpeg + pydub)
* **Information Received**: Original video, original audio track, and synthesized WAV clips.
* **Information Lost**: Excessively long audio tails (previously truncated; now resolved via dynamic speedups).
* **Information Preserved**: Precise timestamp alignments and background background noise track (via adjustable audio bleed-through).
* **Impact on Final Quality**: Assembles the final video. Using dynamic time stretching preserves entire phrases, preventing sentence truncation and maintaining timeline synchronization.

---

## 2. Speaker Preservation Audit

### Preservation Scope
* **Gender & Pitch**: Preserved natively for Hindi (using XTTS). For Telugu (and other fallback/gTTS languages), gender is preserved via autocorrelation fundamental frequency (F0) analysis of the speaker clip:
  * Male speakers (`F0 <= 165 Hz`) are pitch-shifted down by 4 semitones and sped up by `1.26` (preserving natural duration) to transform standard female gTTS voices into deep male voices.
  * Female speakers are processed directly at default gTTS pitches.
* **Speaker Identity & Tone**: Preserved natively for Hindi using the 6s auto-extracted reference clip or user-provided reference. Discarded for Telugu due to XTTS language support constraints.

---

## 3. Telugu Translation & TTS Analysis (Root Cause)

* **Behavior**: Default English-to-Telugu pipeline output resulted in a static female voice, ignoring speaker characteristics.
* **Root Cause**:
  1. **XTTS Language Support**: Coqui XTTS v2 does not natively support Telugu (`te`). The pipeline forced fallback mode for Telugu.
  2. **Missing Fallback Model**: No local Telugu single-speaker fallback model is defined in `FALLBACK_MODELS`.
  3. **gTTS Execution**: The engine defaulted to `gTTS` (Google Text-to-Speech), which communicates with a cloud API.
  4. **Gender & Reference Loss**: `gTTS` does not accept reference clips (`speaker_wav`) and returns a default female Telugu voice, disregarding the source speaker's attributes.

---

## 4. Emotion Preservation & Timing Audits

* **Emotion Fidelity**: Mapped cinematic emotion labels (e.g. `melancholic`, `tense`, `intense`) to speed/pitch offsets. Applying these offsets as post-processing steps directly alters the prosody (pitch-shifting and speedups) of synthesized segments.
* **Timing & Drift**:
  * English to Telugu translations expand syllable count, causing synthesized clips to exceed original segment durations.
  * **Timing Preservation**: The `ComposerAgent` now computes the duration ratio (`tts_duration / source_duration`) for every segment. If it exceeds 1.0, the segment is automatically compressed (up to 1.5x) using `speedup` to fit the timeline, avoiding truncation.
