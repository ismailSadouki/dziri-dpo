# Qwen2.5-1.5B-Instruct — Algerian Darija DPO

## Model

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Training stages:
  1. supervised fine-tuning
  2. direct preference optimization
- Language/domain: Algerian Darija
- Training method: LoRA / QLoRA
- License: Apache-2.0

## Motivation

This model is adapted to Algerian Darija using human preference data.

The objective is to investigate whether preference optimization improves
response quality, helpfulness, and alignment beyond supervised fine-tuning.

## Preference dataset

- Dataset name: TBD
- Dataset version: TBD
- Number of preference pairs: TBD
- Number of annotators: TBD
- Double-annotated examples: TBD
- Agreement statistic: TBD
- Construction procedure: TBD
- Preference criteria: TBD

## DPO configuration

- Seed: `42`
- Beta: `0.1`
- Maximum sequence length: `512`
- Maximum prompt length: `256`
- Per-device batch size: `1`
- Gradient accumulation: `8`
- Learning rate: `5e-6`
- Gradient clipping: `1.0`
- Gradient checkpointing: enabled

## LoRA

- Rank: `16`
- Alpha: `32`
- Dropout: `0.05`
- Target modules:
  - `q_proj`
  - `k_proj`
  - `v_proj`
  - `o_proj`

## Quantization

- Method: bitsandbytes
- 4-bit: enabled
- Quantization type: NF4
- Double quantization: enabled
- Compute dtype: BF16

## Evaluation

The model will be compared against:

1. Base model
2. SFT model
3. DPO model

Evaluation will include, where applicable:

- preference accuracy
- response quality
- Algerian Darija linguistic quality
- failure taxonomy
- calibration/reliability analysis
- qualitative examples

## DPO health metrics

Training diagnostics will include:

- DPO loss
- reward accuracy
- chosen reward
- rejected reward
- reward margin
- preference accuracy on held-out data

Training metrics will not be interpreted independently of held-out
evaluation.

## Hardware

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
- LoRA configuration
- DPO beta
- Software versions
- Peak GPU memory

## Limitations

Preference optimization can amplify biases or annotation artifacts present
in the preference dataset.

Performance should therefore be interpreted together with annotation
agreement, disagreement analysis, held-out evaluation, and qualitative
failure analysis.