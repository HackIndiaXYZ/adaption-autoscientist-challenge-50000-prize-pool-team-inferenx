# CineLocalAI — GitIgnore Design & Recommendations

This document outlines the design structure, rules, and tracking recommendations configured within the production-grade `.gitignore` file.

---

## 1. Selected GitIgnore Rules

The repository root `.gitignore` file is organized into distinct logical zones:

### Python Caches
```gitignore
__pycache__/
*.pyc
*.pyo
*.pyd
.pytest_cache/
```
*Rationale*: Prevents developer-specific compiled python bytecodes and testing caches from polluting code logs.

### Virtual Environments
```gitignore
.venv/
venv/
env/
ENV/
```
*Rationale*: Ensures local virtual environment directory mounts (libraries and dependencies) are not tracked.

### Large Weights and Model Checkpoints
```gitignore
models/base_models/
models/checkpoints/
models/adaption_mixtral_lora/*.safetensors
models/adaption_mixtral_lora/*.bin
```
*Rationale*: Excludes huge deep-learning weights (such as `adapter_model.safetensors` - `109.1 MB`) from standard git tracking. This keeps the initial repository cloning quick and lightweight.

### Media Outputs & Temporary Caching
```gitignore
outputs/
data/checkpoints/
data/transcripts/
logs/
*.log
*.tmp
```
*Rationale*: Excludes transient intermediate audio cuts and compiled MP4 validations.

### Secret Key Files
```gitignore
.env
.env.*
*.key
*.pem
```
*Rationale*: Prevents any accidentally saved local keys or service access tokens from leaking to public spaces.

---

## 2. Model Weight Management Guide

To manage model weights (like `adapter_model.safetensors`):
1. **GitHub Hard Limits**: GitHub will automatically reject any commit containing files larger than **`100 MB`**. Since the LoRA adapter weight is `109.1 MB`, it cannot be pushed via standard git.
2. **Alternative A: Git LFS**: Track `.safetensors` using Git Large File Storage:
   ```bash
   git lfs install
   git lfs track "models/adaption_mixtral_lora/*.safetensors"
   ```
3. **Alternative B: Hugging Face Hosting (Recommended)**: Store the weights on Hugging Face (under `Balrajukonne2629/mixtral-8x7b-cinelocalai-lora`) and add them to `.gitignore`. Tokenizer files, chat templates, and config files remain tracked in the git repo, allowing users to pull weights dynamically at runtime.
