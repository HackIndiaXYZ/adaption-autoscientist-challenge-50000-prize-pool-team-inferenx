# CineLocalAI Mixtral LoRA Adapter Weights

The model weights (`adapter_model.safetensors`) are hosted externally on Hugging Face to keep the repository lightweight and comply with GitHub file size boundaries.

* **Hugging Face Model Link**: [balrajukonne/cinelocalai-mixtral-lora](https://huggingface.co/balrajukonne/cinelocalai-mixtral-lora)

---

## 1. Download Instructions

### Manual Download
1. Navigate to the Hugging Face Repository [Files and Versions tab](https://huggingface.co/balrajukonne/cinelocalai-mixtral-lora/tree/main).
2. Download `adapter_model.safetensors` (~109 MB).
3. Place the file inside the local directory:
   `models/adaption_mixtral_lora/`

### Command Line Download (using huggingface-cli)
```bash
pip install huggingface_hub
huggingface-cli download balrajukonne/cinelocalai-mixtral-lora adapter_model.safetensors --local-dir models/adaption_mixtral_lora
```

---

## 2. Loading Instructions

CineLocalAI automatically resolves the model weights if `adapter_model.safetensors` is present in the `models/adaption_mixtral_lora/` directory.

### In Code (Transformers & PEFT)
To load this adapter model manually in Python:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

model_dir = "models/adaption_mixtral_lora/"

# Load base model
base_model = AutoModelForCausalLM.from_pretrained(
    "mistralai/Mixtral-8x7B-Instruct-v0.1",
    torch_dtype=torch.float16,
    device_map="auto"
)

# Load fine-tuned adapter weights
model = PeftModel.from_pretrained(base_model, model_dir)
tokenizer = AutoTokenizer.from_pretrained(model_dir)
```
