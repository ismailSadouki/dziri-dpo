# SFT Stage 3 — LoRA vs QLoRA

## Setup

- Model: Qwen/Qwen2.5-1.5B-Instruct
- Target modules: all-linear
- LoRA rank: 16
- LoRA alpha: 32
- LoRA dropout: 0.05
- Seed: 42
- Training steps: 100
- Train examples: 176
- Eval examples: 44
- Max sequence length: 512
- Hardware: RTX 3050 Laptop, 3.68 GiB usable VRAM

## Results

| Method | Eval loss | Token accuracy | Peak allocated VRAM | Wall time | Status |
|---|---:|---:|---:|---:|---|
| LoRA BF16 | — | — | 3.02 GB before OOM | 2.39 s | OOM |
| QLoRA NF4 | 2.9599 | 0.4311 | 2.51 GB | 424.70 s | PASS |

### LoRA BF16

The model loaded successfully with full BF16 weights and 18,464,768
trainable parameters (1.1820%).

Training failed on the first training step with CUDA OOM while computing
the chunked cross-entropy loss. The failed allocation was 892 MiB with
551.56 MiB free.

Therefore, no BF16 quality metrics are reported.

### QLoRA NF4

The identical training configuration was previously completed during
Stage 2 rank-16. The Stage 2 and Stage 3 QLoRA configurations differ
only in run name and output directory, so the Stage 2 result is reused
for this controlled method comparison.

## Decision

QLoRA NF4 is selected as the feasible SFT method for the remaining
experiments on the current GPU.

This comparison establishes hardware feasibility, not that QLoRA has
superior model quality to BF16 LoRA, since BF16 did not complete a
training run.

## Caveats

- One seed.
- 100 training steps.
- 44-example validation set.
- Evaluation uses token accuracy and loss, not human-quality judgments.
- BF16 LoRA was evaluated for feasibility only because it OOMed before
  completing the first step.