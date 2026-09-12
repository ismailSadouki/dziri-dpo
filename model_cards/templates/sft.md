# Qwen2.5-1.5B-Instruct — Algerian Darija SFT

## Model

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Model revision: `main`
- Task: supervised fine-tuning
- Language/domain: Algerian Darija
- Training method: LoRA / QLoRA
- License: Apache-2.0

## Motivation

This model is adapted to Algerian Darija through supervised instruction
fine-tuning.

The goal is to measure how much targeted Algerian Darija instruction data
improves generation quality relative to the original multilingual
instruction model.

## Training configuration

- Seed: `42`
- Sequence length: `512`
- Epochs: `1`
- Per-device batch size: `1`
- Gradient accumulation: `8`
- Learning rate: `5e-5`
- Weight decay: `0.0`
- Gradient clipping: `1.0`
- Gradient checkpointing: enabled

### LoRA

- Rank: `16`
- Alpha: `32`
- Dropout: `0.05`
- Target modules:
  - `q_proj`
  - `k_proj`
  - `v_proj`
  - `o_proj`

### Quantization

- Method: bitsandbytes
- 4-bit: enabled
- Quantization type: NF4
- Double quantization: enabled
- Compute dtype: BF16

## Dataset

- Dataset: TBD
- Dataset version: TBD
- Number of training examples: TBD
- Number of validation examples: TBD
- Construction procedure: TBD
- Annotation procedure: TBD

## Evaluation

Evaluation will compare:

1. Base model
2. SFT model
3. DPO model

Metrics and evaluation datasets will be documented separately.

## Hardware

Hardware used for training:

- GPU: TBD
- VRAM: TBD
- CUDA: TBD

## Reproducibility

Each experiment records:

- Git commit
- Model revision
- Tokenizer revision
- Dataset version
- Random seed
- Adapter configuration
- Software versions
- Peak GPU memory

## Limitations

This model is intended for research on Algerian Darija NLP.

Performance may vary across:

- Algerian regional varieties
- code-switching patterns
- Arabic/French mixtures
- spelling conventions
- informal social-media language
- topics underrepresented in the training data

No claim of general linguistic competence should be made from the
training loss alone.