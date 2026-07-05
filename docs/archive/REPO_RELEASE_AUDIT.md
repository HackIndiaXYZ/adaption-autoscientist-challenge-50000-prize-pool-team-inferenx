# CineLocalAI — Repository Release Audit

This document details the final packaging layout, file audit classification, and cleanup recommendations for preparing the CineLocalAI repository for open-source GitHub release.

---

## 1. Folder Structure Classification

| File / Folder Path | Type | Action | Auditing Details & Recommendations |
| :--- | :--- | :---: | :--- |
| **`agents/`** | Code | **KEEP** | Core multi-agent pipeline files (`tts_agent.py`, `composer_agent.py`, `emotion_tagger.py`). |
| **`orchestrator/`** | Code | **KEEP** | Pipeline execution orchestrator (`pipeline.py`) and router (`model_router.py`). |
| **`config/`** | Config | **KEEP** | Environment settings (`settings.yaml`). |
| **`docs/`** | Docs | **KEEP** | Core documentation folder. Clean historical drafts into `docs/archive/`. |
| **`tests/`** | Code | **KEEP** | Production validation test suites. |
| **`data/sample/`** | Media | **KEEP** | Sample media files (rename `demo/` folder to `data/sample/` for clean structure). |
| **`models/adaption_mixtral_lora/`** | Model | **KEEP / IGNORE** | Keep tokenizer configuration files; upload the large weight safetensors to Hugging Face and ignore locally. |
| **`outputs/`** | Media | **DELETE** | Temporary run outputs generated during development (clear folder but keep structure). |
| **`data/checkpoints/`** | Cache | **DELETE** | Stage caching files and run histories. |
| **`data/transcripts/`** | Cache | **DELETE** | Temporary text transcripts generated from Whisper runs. |
| **`temp/` / `logs/` / `cache/`** | Cache | **DELETE** | General runtime cache folders and session logs. |
| **`__pycache__/` / `.pytest_cache/`**| Cache | **DELETE** | Python byte-compiled cache folders. |

---

## 2. Safe Clean-Up Action Plan (Command Line Execution)

To safely clean and archive files without deleting critical historical data automatically, execute the following PowerShell instructions:

### Step A: Create Archive and Move Documentation
```powershell
# Create documentation archive directory
New-Item -ItemType Directory -Force -Path docs/archive

# Archive historical reports from the workspace root
Move-Item -Force -Path PROJECT_AUDIT.md docs/archive/
Move-Item -Force -Path FINAL_VALIDATION_REPORT.md docs/archive/
Move-Item -Force -Path FINAL_RISK_REVIEW.md docs/archive/
Move-Item -Force -Path FINAL_SUBMISSION_DECISION.md docs/archive/
Move-Item -Force -Path HACKATHON_SUBMISSION_SCORE.md docs/archive/
```

### Step B: Standardize Sample Media Path
```powershell
# Create standardized data directory
New-Item -ItemType Directory -Force -Path data/sample

# Move sample video and reference audio into it
Move-Item -Force -Path demo/sample.mp4 data/sample/
Move-Item -Force -Path demo/speaker.wav data/sample/
Remove-Item -Recurse -Force -Path demo/
```

### Step C: Purge Cached Directories
```powershell
# Purge build caches and temporary runs
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue -Path data/checkpoints/
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue -Path data/transcripts/
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue -Path outputs/tts/*
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue -Path outputs/final/*
Get-ChildItem -Path . -Filter __pycache__ -Recurse | Remove-Item -Recurse -Force
```
