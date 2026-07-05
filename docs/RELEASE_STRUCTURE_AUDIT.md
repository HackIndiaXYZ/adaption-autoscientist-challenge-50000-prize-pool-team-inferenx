# CineLocalAI — Release Structure Audit

This report presents a final audit of the files and directories inside the `cinelocalai/` repository folder before release.

---

## 1. Directory Structure

```text
cinelocalai/
├── agents/                     # Core pipeline execution agents
├── config/                     # settings.yaml file
├── data/                       # Datasets
│   ├── gold_dataset/           # 204 gold dialogue records
│   └── dataset_schema.json     # Fine-tuning JSONL schema
├── docs/                       # Project documentation
│   └── archive/                # Archived reports and logs
│       └── dataset_history/    # Archived train/test/validation sets
├── models/                     # PEFT Model configs and pointers
│   └── adaption_mixtral_lora/  # LoRA adapter configs and MODEL_LINK.md
├── orchestrator/               # Pipeline execution and model routing logic
├── outputs/                    # Output directory (gitignored)
├── tests/                      # Automated validations
├── filter_dataset.py           # Dataset cleaning utility
├── main.py                     # Execution entrypoint
├── requirements.txt            # Python requirements
├── LICENSE                     # MIT License
└── README.md                   # Upgraded README
```

---

## 2. File Audit Classification

### Keep (Tracked by Git)
* **Source Logic**: `agents/`, `orchestrator/`, `main.py`, `filter_dataset.py`.
* **Configurations**: `config/settings.yaml`, `requirements.txt`.
* **Gold Data & Schema**: `data/dataset_schema.json`, `data/gold_dataset/cinelocalai_gold.jsonl`.
* **Documentation**: `README.md`, `LICENSE`, `docs/*.md`.
* **LoRA Metadata**: `models/adaption_mixtral_lora/` (except `.safetensors` files).

### Ignore (Excluded in `.gitignore`)
* **Bytecode**: `__pycache__/`, `*.pyc`, `*.pyo`, `*.pyd`.
* **Environments**: `.venv/`, `venv/`, `env/`.
* **Cache Directories**: `data/checkpoints/`, `data/transcripts/`, `.pytest_cache/`.
* **Temp/Output files**: `outputs/`, `logs/`, `*.log`, `*.tmp`.
* **Model Weights**: `adapter_model.safetensors`, `*.ckpt`, `*.pt`, `*.pth`.

### Archive (Moved to `docs/archive/`)
* **Historical Audit Reports**: `PROJECT_AUDIT.md`, `PHASE0_STATUS.md`, `audit_summary.json`.
* **Dataset History**: `train.jsonl`, `test.jsonl`, `validation.jsonl` (under `docs/archive/dataset_history/`).
* **Validation logs**: `FINAL_VALIDATION_REPORT.md`, `PRODUCTION_RISKS.md`, etc.

---

## 3. Estimated Repository Size After Cleanup

* **Raw Total Size (Including weights and outputs)**: `~493.3 MB`
* **Excluding Ignores (Virtual Env & Dubbed MP4s)**: `~150.8 MB`
* **Clean Release Size (Hugging Face Ignored Weights)**: **`~38.3 MB`** (Includes code, schema, gold dataset, and configs).
