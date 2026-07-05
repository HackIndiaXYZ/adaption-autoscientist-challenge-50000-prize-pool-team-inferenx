# CineLocalAI — Production Risks

This document outlines the remaining engineering risks, severity, probability, and mitigations for the CineLocalAI pipeline before deployment or hackathon submission.

---

## 1. Production Risk Matrix

| Risk Area | Severity | Probability | Risk Description | Mitigation Strategy |
| :--- | :---: | :---: | :--- | :--- |
| **gTTS Web Dependency** | **Medium** | **Medium** | Fallback mode for unsupported XTTS languages (e.g. Telugu) uses gTTS, which requires internet access. A network outage breaks offline capabilities. | Package lightweight local VITS or Festvox models for Telugu to enable 100% offline coverage for all standard Indian languages. |
| **Grammatical Gender Bias** | **Low** | **High** | Offline translators (NLLB/Marian) can output biased grammatical suffixes (e.g., using feminine suffixes for a male speaker) because they lack speaker identity context. | Feed the estimated F0 gender category into the translation model (either via prefix tags or instruction-tuned prompts) to guide gender agreement. |
| **Chipmunk Speedup Effect** | **Low** | **Medium** | Extremely long translations compressed past `1.3x` via pydub's `speedup` can sound unnatural or high-pitched. | Integrate a length-capping heuristic in translation generation: enforce maximum syllable count rules to prevent length explosions before TTS. |
| **Single-Speaker Assumption** | **Medium** | **Medium** | The dynamic speaker selection extracts one dominant voice print. In multi-speaker dialogs, a single voice print is cloned, causing different speakers to sound alike. | Integrate a lightweight diarization step (e.g. WhisperX or simple spectral clustering) to split segments by speaker ID before voice synthesis. |
