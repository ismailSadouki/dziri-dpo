# Colab/T4 Environment

## 1. Install

```bash
pip install -U \
  "transformers==5.15.0" \
  "trl==1.10.0" \
  "peft==0.20.0" \
  "bitsandbytes==0.50.1" \
  "datasets==5.0.1" \
  "accelerate==1.10.1" \
  "pyyaml"
```

## 2. Verify

```python
import torch
import transformers
import trl
import peft
import bitsandbytes
import datasets
import accelerate
import yaml

print("PyTorch:", torch.__version__)
print("CUDA:", torch.version.cuda)
print("CUDA available:", torch.cuda.is_available())

if torch.cuda.is_available():
    print("GPU:", torch.cuda.get_device_name(0))
    print("BF16:", torch.cuda.is_bf16_supported())

print("Transformers:", transformers.__version__)
print("TRL:", trl.__version__)
print("PEFT:", peft.__version__)
print("bitsandbytes:", bitsandbytes.__version__)
print("Datasets:", datasets.__version__)
print("Accelerate:", accelerate.__version__)
print("PyYAML:", yaml.__version__)
```

## 3. Expected hardware

The production experiments are designed around a single NVIDIA T4
environment.

Expected:

* GPU: NVIDIA T4
* VRAM: approximately 16 GiB
* CUDA: determined by the Colab runtime
* 4-bit NF4: enabled
* BF16 compute: preferred when supported

## 4. Hugging Face authentication

Authentication is optional for public models.

For higher Hub rate limits:

```python
from huggingface_hub import login

login()
```

Do not hard-code tokens in notebooks, scripts, configuration files,
or Git repositories.

## 5. Model smoke test

From the repository root:

```bash
python scripts/load_model.py --config configs/model.yaml
```

The smoke test must verify:

* model loading
* tokenizer loading
* chat template
* generation
* GPU placement
* peak GPU memory

## 6. Reproducibility

Record the following for every experiment:

* Git commit
* model revision
* tokenizer revision
* dataset version
* random seed
* LoRA configuration
* quantization configuration
* software versions
* GPU
* peak GPU memory

