# CineLocalAI — Repository Packaging Audit

This document presents a comprehensive review of the folders and files in the CineLocalAI repository, identifying which assets should be kept, moved, or deleted to prepare the repository for public GitHub release.

---

## 1. Directory Tree & Auditing Decisions

| Path | File Type / Description | Size / Scope | Action | Rationale |
| :--- | :--- | :---: | :---: | :--- |
| **`agents/`** | Core pipeline agent classes | Source Code | **KEEP** | Essential application logic (`tts_agent.py`, `composer_agent.py`, etc.). |
| **`orchestrator/`** | Core orchestrator and pipeline | Source Code | **KEEP** | Coordinates the stage transitions (`pipeline.py`, `model_router.py`). |
| **`config/`** | Settings and hyperparameters | Config | **KEEP** | Holds `settings.yaml` for setting model layers and target modes. |
| **`docs/`** | Documentation markdown files | Documentation | **KEEP** | Critical for user onboarding and hackathon judging review. |
| **`evaluation/`** | Metrics and data checks | Evaluation | **KEEP** | Code/scripts used to validate output fidelity. |
| **`demo/`** | Video inputs and validation | Testing | **KEEP** | Includes `sample.mp4` and `speaker.wav` needed for end-to-end tests. |
| **`models/`** | Model weights / LoRA adapters | PEFT Model | **KEEP** | Holds `adaption_mixtral_lora/` weights (tokenizer, config, safetensors). |
| **`data/adaption_dataset/`** | Audited raw JSONL dataset | Dataset | **KEEP** | The baseline dataset retrieved from Adaption Labs. |
| **`data/gold_dataset/`** | Filtered dataset | Dataset | **KEEP** | Contains the 204 filtered gold dialogue records (`cinelocalai_gold.jsonl`). |
| **`data/transcripts/`** | Debug transcript outputs | Output Log | **DELETE** | Temporary text files generated during verification runs; clear before git push. |
| **`data/checkpoints/`** | Intermediate caching folders | Cache | **DELETE** | Stage caching folders (`test_1_male_hi/`, `verify_hi/`, etc.) that take up disk space. |
| **`outputs/tts/`** | Temp synthesized segment WAVs | Cache | **DELETE** | Temporary segment audio clips overwritten by each run; keep folder empty with `.gitkeep`. |
| **`outputs/final/`** | Final dubbed videos and JSONs | Dubbed Media | **MOVE** | Keep only final demo assets (`test_1_male_hi_dubbed.mp4`, etc.) and delete temporary run items. |
| **`filter_dataset.py`** | Dataset cleaning script | Utility | **KEEP** | Key tool for filtering the Adaption Labs dataset. |
| **`main.py`** | CLI execution entrypoint | Utility | **KEEP** | Entry point for running the pipeline. |
| **`requirements.txt`** | Dependency definitions | Dependency | **KEEP** | Crucial for establishing the virtual environment. |

---

## 2. Clean-Up Action Plan

Before executing the final git push to GitHub:
1. Run `git clean -fd` or manually remove the directories `data/checkpoints/` and `data/transcripts/`.
2. Clear all synthesized segment files inside `outputs/tts/`, keeping only the `.gitkeep` file.
3. Consolidate `outputs/final/` to keep only the four key validation runs (`test_1` through `test_4`), deleting debug and validation experiment files (like `demo_run_001`, `verify_hi`, etc.) to reduce the overall repository transfer size by approximately **300 MB**.
