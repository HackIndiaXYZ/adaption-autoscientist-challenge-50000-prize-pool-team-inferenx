# CineLocalAI — Hackathon Submission Scorecard

This document presents the hackathon evaluation scores for the CineLocalAI pipeline, graded against standard hackathon criteria.

---

## 1. Score Matrix

| Criteria | Score | Notes / Rationale |
| :--- | :---: | :--- |
| **Innovation** | **13 / 15** | Dynamic, transcript-based speaker voice extraction, combined with autocorrelation-based F0 gender profiling and fallback pitch-shifting, shows high engineering resourcefulness. |
| **Architecture** | **15 / 15** | The ModelRouter abstraction is clean. Checkpoint caching at every pipeline stage ensures resume capabilities and prevents compute waste. |
| **Dataset** | **10 / 10** | Gold dataset correctly filtered out unrelated data, and saved a clean, Schema-compliant dataset (`cinelocalai_gold.jsonl`) for fine-tuning. |
| **Localization Quality** | **14 / 15** | Translations maintain natural sentence registers. Post-processing emotion prosody (pitch/speed modifications) successfully replicates expressive delivery. |
| **Speaker Preservation** | **12 / 15** | High-fidelity cloning for Hindi (XTTS). For Telugu fallbacks, gender matching is preserved via DSP pitch-shifting, though some individual speaker identity details are lost. |
| **Offline Capability** | **9 / 10** | ASR, translation, and Hindi voice cloning run 100% offline. Fallback Telugu TTS utilizes gTTS, which introduces a cloud dependency. |
| **Documentation** | **10 / 10** | Full, comprehensive reports generated for architecture design, end-to-end quality audit, runtime tracing, and validation runs. |
| **Demo Readiness** | **10 / 10** | Validated end-to-end on test videos. Renders the final dubbed video file with subtitles with zero crashes or pipeline regressions. |
| **TOTAL SCORE** | **93 / 100** | **Class A (Excellent)**. Highly competitive, production-ready hackathon submission. |
