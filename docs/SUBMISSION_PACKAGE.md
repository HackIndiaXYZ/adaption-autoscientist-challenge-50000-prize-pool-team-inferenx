# CineLocalAI — Final Submission Packaging List

This document lists all the assets, models, datasets, and documentation files prepared for the final hackathon submission.

---

## 1. Dataset Assets

* **File Name**: `data/gold_dataset/cinelocalai_gold.jsonl`
* **File Size**: `5.95 MB` (5,945,655 bytes)
* **Record Count**: `204` high-quality movie dialogue pairs.
* **Purpose**: Fine-tuning dataset for machine translation and dialog localization models (Hindi and Telugu).
* **Kaggle Dataset URL**: `https://www.kaggle.com/datasets/balrajukonne2629/cinelocalai-gold-localization`

---

## 2. Model Assets

* **Directory**: `models/adaption_mixtral_lora/`
* **Total Size**: `~112.5 MB`
* **Key Files**:
  - `adapter_model.safetensors` (`109.1 MB`): Fine-tuned low-rank adapter weights.
  - `tokenizer.json` (`3.5 MB`): Custom tokenizer configurations.
  - `adapter_config.json` (`833 bytes`): Hyperparameters ($r=8$, $\alpha=16$).
  - `chat_template.jinja` (`1.05 KB`): Conversation prompt layout.
* **Purpose**: Parameter-Efficient Fine-Tuning (PEFT) adapter to enhance Mixtral dialogue localization.
* **Hugging Face Model URL**: `https://huggingface.co/Balrajukonne2629/mixtral-8x7b-cinelocalai-lora`

---

## 3. Documentation Assets

* **[ARCHITECTURE.md](file:///c:/Users/konne%20balraju/OneDrive/Desktop/AI%20Auto%20Scientis%20HACKATHON/cinelocalai/docs/ARCHITECTURE.md)**: Explains the multi-agent pipeline and model router.
* **[QUALITY_AUDIT.md](file:///c:/Users/konne%20balraju/OneDrive/Desktop/AI%20Auto%20Scientis%20HACKATHON/cinelocalai/docs/QUALITY_AUDIT.md)**: Audits the stage-by-stage data lifecycle and loss.
* **[SPEAKER_VALIDATION.md](file:///c:/Users/konne%20balraju/OneDrive/Desktop/AI%20Auto%20Scientis%20HACKATHON/cinelocalai/docs/SPEAKER_VALIDATION.md)**: Details validation runs, F0 results, and gender categorization.
* **[TELUGU_RUNTIME_TRACE.md](file:///c:/Users/konne%20balraju/OneDrive/Desktop/AI%20Auto%20Scientis%20HACKATHON/cinelocalai/docs/TELUGU_RUNTIME_TRACE.md)**: Details the exact runtime path for Telugu fallback synthesis.
* **[FINAL_VALIDATION_REPORT.md](file:///c:/Users/konne%20balraju/OneDrive/Desktop/AI%20Auto%20Scientis%20HACKATHON/cinelocalai/docs/FINAL_VALIDATION_REPORT.md)**: Documents regression tests on Hindi and Telugu.
* **[PRODUCTION_RISKS.md](file:///c:/Users/konne%20balraju/OneDrive/Desktop/AI%20Auto%20Scientis%20HACKATHON/cinelocalai/docs/PRODUCTION_RISKS.md)**: Analyzes deployment risks (gTTS, single-speaker assumption) and mitigations.

---

## 4. Demo Media Assets

Located under `outputs/final/`:
* **`test_1_male_hi_dubbed.mp4`** (Hindi Male Demo, XTTS)
* **`test_2_female_hi_dubbed.mp4`** (Hindi Female Demo, XTTS)
* **`test_3_male_te_dubbed.mp4`** (Telugu Male Demo, pitch-shifted gTTS Fallback)
* **`test_4_female_te_dubbed.mp4`** (Telugu Female Demo, default gTTS Fallback)
* Corresponding metadata JSON files and subtitles SRT files.

---

## 5. Deployment Repositories

* **GitHub Repository URL**: `https://github.com/Balrajukonne2629/cinelocalai`
