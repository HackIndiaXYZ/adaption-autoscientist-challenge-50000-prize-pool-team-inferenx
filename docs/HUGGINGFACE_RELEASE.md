# CineLocalAI — Hugging Face Model Card Release

This model card details the packaging, training configuration, and usage guidelines for the fine-tuned LoRA adapter model.

---

## 1. Model Card Details

### Model Summary
* **Base Model**: `mistralai/Mixtral-8x7B-Instruct-v0.1`
* **Fine-Tuning Method**: Parameter-Efficient Fine-Tuning (PEFT) using LoRA (Low-Rank Adaptation).
* **Target Modules**: `q_proj`, `v_proj`, `k_proj`, `o_proj`
* **Training Dataset Size**: 204 highly curated gold movie-dialogue records (`cinelocalai_gold.jsonl`).
* **Supported Languages**: English (`en`) to Hindi (`hi`) and Telugu (`te`) translation.

---

## 2. Usage Example

To load and run inference with this adapter model:

```python
import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

base_model_id = "mistralai/Mixtral-8x7B-Instruct-v0.1"
lora_adapter_path = "models/adaption_mixtral_lora/"

# 1. Load Tokenizer
tokenizer = AutoTokenizer.from_pretrained(lora_adapter_path)

# 2. Load Base Model (using FP16 or 8-bit quantization for GPU memory optimization)
base_model = AutoModelForCausalLM.from_pretrained(
    base_model_id,
    torch_dtype=torch.float16,
    device_map="auto"
)

# 3. Load Fine-Tuned LoRA Adapter
model = PeftModel.from_pretrained(base_model, lora_adapter_path)

# 4. Generate Localized Text
text = "Speaker: Stay committed, stay strong, and relentlessly pursue your dreams with all your heart."
inputs = tokenizer(text, return_tensors="pt").to("cuda")
with torch.no_grad():
    outputs = model.generate(**inputs, max_new_tokens=64)
print(tokenizer.decode(outputs[0], skip_special_tokens=True))
```

---

## 3. Training Hyperparameters

From `trainer_state.json` and `adapter_config.json`:
* **Rank ($r$)**: `8`
* **LoRA Alpha ($\alpha$)**: `16`
* **LoRA Dropout**: `0.05`
* **Batch Size**: `8`
* **Optimizer**: `adamw_torch`
* **Learning Rate**: `2e-4`

---

## 4. Known Limitations & Recommendations

* **Hardware Resource Bounds**: The base model `Mixtral-8x7B` is a Mixture of Experts model requiring large amounts of VRAM. Quantization (e.g. 4-bit/8-bit via `bitsandbytes`) is highly recommended for consumer-grade GPU cards.
* **Domain Specificity**: The adapter is highly optimized for localized movie dialogue (colloquial registers, cultural references). It is not recommended for formal legal, technical, or document translation tasks.
* **License**: Governed by the original Apache-2.0 license of the base Mixtral model.
