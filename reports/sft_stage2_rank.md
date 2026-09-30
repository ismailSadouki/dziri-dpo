# SFT Stage 2 — LoRA Rank Sweep

## Objective

Evaluate LoRA ranks `{8, 16, 32, 64}` using the provisional Stage 1
target-module configuration `all-linear`.

Only the LoRA rank changes between runs.

## Fixed configuration

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Target modules: `all-linear`
- Quantization: QLoRA NF4
- Compute dtype: BF16# SFT Stage 2 — LoRA Rank Sweep

## Objective

Evaluate LoRA ranks `{8, 16, 32, 64}` using the provisional Stage 1
target-module configuration `all-linear`.

Only the LoRA rank changes between runs.

## Fixed configuration

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Target modules: `all-linear`
- Quantization: QLoRA NF4
- Compute dtype: BF16
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Learning rate: `5e-5`
- Maximum sequence length: `512`
- Gradient accumulation: `8`
- Training steps: `100`
- Seed: `42`
- Dataset and train/validation split: unchanged from Stage 1

## Results

| Rank | Trainable params | Trainable % | Train loss | Eval loss | Eval token accuracy | Peak VRAM | Wall time | Tokens/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 9,232,384 | 1.0283% | 3.0323 | 2.9607 | 0.4302 | 2.44 GB | 376.00 s | 282.08 |
| 16 | 18,464,768 | 2.0356% | 3.0369 | 2.9599 | **0.4311** | 2.51 GB | 424.70 s | 249.74 |
| 32 | 36,929,536 | 3.9900% | 3.0339 | **2.9591** | 0.4306 | 2.64 GB | 375.49 s | **282.56** |
| 64 | 73,859,072 | 7.6739% | 3.0432 | 2.9623 | 0.4299 | 2.97 GB | 393.73 s | 269.34 |

## Observations

Increasing the LoRA rank substantially increases the number of trainable
parameters:

- r=8 → 9.23M
- r=16 → 18.46M
- r=32 → 36.93M
- r=64 → 73.86M

The validation metrics remain very close across all four ranks.

The lowest validation loss in this experiment is obtained by r=32
(`2.9591`), while the highest validation token accuracy is obtained by
r=16 (`0.4311`).

The r=64 configuration does not improve either validation metric and
requires the largest adapter and highest peak allocated VRAM.

The measured throughput also does not improve systematically with rank.
The observed values range from approximately 249.74 to 282.56 tokens/sec.

## Provisional rank selection

For subsequent experiments, **rank 16 is retained as the practical
provisional rank**.

The reason is that r=16 achieves the highest validation token accuracy
while avoiding the substantially larger parameter and memory budgets of
r=32 and r=64. Its validation loss is also essentially indistinguishable
from r=32 in this short experiment:

- r=16: `2.9599`
- r=32: `2.9591`

The difference is only `0.0008` validation loss.

This is a provisional engineering choice, not evidence that r=16 is
universally optimal.

## Limitations

This is an exploratory rank sweep:

1. Only one seed (`42`) was evaluated.
2. Each configuration was trained for only 100 steps.
3. The validation split contains 44 examples.
4. Token-level accuracy is not a human evaluation of response quality.
5. The observed differences between ranks are very small.
6. No statistical significance test is appropriate for treating these
   four single-run results as definitive.
7. The final headline configuration still requires evaluation with
   three seeds.

## Artifacts

### Configurations

- `configs/sft/stage2_rank/rank8.yaml`
- `configs/sft/stage2_rank/rank16.yaml`
- `configs/sft/stage2_rank/rank32.yaml`
- `configs/sft/stage2_rank/rank64.yaml`

### Run summaries

- `outputs/sft_stage2_rank8/run_summary.json`
- `outputs/sft_stage2_rank16/run_summary.json`
- `outputs/sft_stage2_rank32/run_summary.json`
- `outputs/sft_stage2_rank64/run_summary.json`

## Stage 2 conclusion

The rank sweep does not show a meaningful quality improvement from
increasing rank beyond 16 under the tested conditions.

Rank 16 is therefore carried forward as the provisional rank for
Stage 3, where the next comparison will be:

**LoRA BF16 vs QLoRA NF4 using `all-linear`, r=16.**# SFT Stage 2 — LoRA Rank Sweep

## Objective

Evaluate LoRA ranks `{8, 16, 32, 64}` using the provisional Stage 1
target-module configuration `all-linear`.

Only the LoRA rank changes between runs.

## Fixed configuration

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Target modules: `all-linear`
- Quantization: QLoRA NF4
- Compute dtype: BF16
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Learning rate: `5e-5`
- Maximum sequence length: `512`
- Gradient accumulation: `8`
- Training steps: `100`
- Seed: `42`
- Dataset and train/validation split: unchanged from Stage 1

## Results

| Rank | Trainable params | Trainable % | Train loss | Eval loss | Eval token accuracy | Peak VRAM | Wall time | Tokens/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 9,232,384 | 1.0283% | 3.0323 | 2.9607 | 0.4302 | 2.44 GB | 376.00 s | 282.08 |
| 16 | 18,464,768 | 2.0356% | 3.0369 | 2.9599 | **0.4311** | 2.51 GB | 424.70 s | 249.74 |
| 32 | 36,929,536 | 3.9900% | 3.0339 | **2.9591** | 0.4306 | 2.64 GB | 375.49 s | **282.56** |
| 64 | 73,859,072 | 7.6739% | 3.0432 | 2.9623 | 0.4299 | 2.97 GB | 393.73 s | 269.34 |

## Observations

Increasing the LoRA rank substantially increases the number of trainable
parameters:

- r=8 → 9.23M
- r=16 → 18.46M
- r=32 → 36.93M
- r=64 → 73.86M

The validation metrics remain very close across all four ranks.

The lowest validation loss in this experiment is obtained by r=32
(`2.9591`), while the highest validation token accuracy is obtained by
r=16 (`0.4311`).

The r=64 configuration does not improve either validation metric and
requires the largest adapter and highest peak allocated VRAM.

The measured throughput also does not improve systematically with rank.
The observed values range from approximately 249.74 to 282.56 tokens/sec.

## Provisional rank selection

For subsequent experiments, **rank 16 is retained as the practical
provisional rank**.

The reason is that r=16 achieves the highest validation token accuracy
while avoiding the substantially larger parameter and memory budgets of
r=32 and r=64. Its validation loss is also essentially indistinguishable
from r=32 in this short experiment:

- r=16: `2.9599`
- r=32: `2.9591`

The difference is only `0.0008` validation loss.

This is a provisional engineering choice, not evidence that r=16 is
universally optimal.

## Limitations

This is an exploratory rank sweep:

1. Only one seed (`42`) was evaluated.
2. Each configuration was trained for only 100 steps.
3. The validation split contains 44 examples.
4. Token-level accuracy is not a human evaluation of response quality.
5. The observed differences between ranks are very small.
6. No statistical significance test is appropriate for treating these
   four single-run results as definitive.
7. The final headline configuration still requires evaluation with
   three seeds.

## Artifacts

### Configurations

- `configs/sft/stage2_rank/rank8.yaml`
- `configs/sft/stage2_rank/rank16.yaml`
- `configs/sft/stage2_rank/rank32.yaml`
- `configs/sft/stage2_rank/rank64.yaml`

### Run summaries

- `outputs/sft_stage2_rank8/run_summary.json`
- `outputs/sft_stage2_rank16/run_summary.json`
- `outputs/sft_stage2_rank32/run_summary.json`
- `outputs/sft_stage2_rank64/run_summary.json`

## Stage 2 conclusion

The rank sweep does not show a meaningful quality improvement from
increasing rank beyond 16 under the tested conditions.

Rank 16 is therefore carried forward as the provisional rank for
Stage 3, where the next comparison will be:

**LoRA BF16 vs QLoRA NF4 using `all-linear`, r=16.**# SFT Stage 2 — LoRA Rank Sweep

## Objective

Evaluate LoRA ranks `{8, 16, 32, 64}` using the provisional Stage 1
target-module configuration `all-linear`.

Only the LoRA rank changes between runs.

## Fixed configuration

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Target modules: `all-linear`
- Quantization: QLoRA NF4
- Compute dtype: BF16
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Learning rate: `5e-5`
- Maximum sequence length: `512`
- Gradient accumulation: `8`
- Training steps: `100`
- Seed: `42`
- Dataset and train/validation split: unchanged from Stage 1

## Results

| Rank | Trainable params | Trainable % | Train loss | Eval loss | Eval token accuracy | Peak VRAM | Wall time | Tokens/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 9,232,384 | 1.0283% | 3.0323 | 2.9607 | 0.4302 | 2.44 GB | 376.00 s | 282.08 |
| 16 | 18,464,768 | 2.0356% | 3.0369 | 2.9599 | **0.4311** | 2.51 GB | 424.70 s | 249.74 |
| 32 | 36,929,536 | 3.9900% | 3.0339 | **2.9591** | 0.4306 | 2.64 GB | 375.49 s | **282.56** |
| 64 | 73,859,072 | 7.6739% | 3.0432 | 2.9623 | 0.4299 | 2.97 GB | 393.73 s | 269.34 |

## Observations

Increasing the LoRA rank substantially increases the number of trainable
parameters:

- r=8 → 9.23M
- r=16 → 18.46M
- r=32 → 36.93M
- r=64 → 73.86M

The validation metrics remain very close across all four ranks.

The lowest validation loss in this experiment is obtained by r=32
(`2.9591`), while the highest validation token accuracy is obtained by
r=16 (`0.4311`).

The r=64 configuration does not improve either validation metric and
requires the largest adapter and highest peak allocated VRAM.

The measured throughput also does not improve systematically with rank.
The observed values range from approximately 249.74 to 282.56 tokens/sec.

## Provisional rank selection

For subsequent experiments, **rank 16 is retained as the practical
provisional rank**.

The reason is that r=16 achieves the highest validation token accuracy
while avoiding the substantially larger parameter and memory budgets of
r=32 and r=64. Its validation loss is also essentially indistinguishable
from r=32 in this short experiment:

- r=16: `2.9599`
- r=32: `2.9591`

The difference is only `0.0008` validation loss.

This is a provisional engineering choice, not evidence that r=16 is
universally optimal.

## Limitations

This is an exploratory rank sweep:

1. Only one seed (`42`) was evaluated.
2. Each configuration was trained for only 100 steps.
3. The validation split contains 44 examples.
4. Token-level accuracy is not a human evaluation of response quality.
5. The observed differences between ranks are very small.
6. No statistical significance test is appropriate for treating these
   four single-run results as definitive.
7. The final headline configuration still requires evaluation with
   three seeds.

## Artifacts

### Configurations

- `configs/sft/stage2_rank/rank8.yaml`
- `configs/sft/stage2_rank/rank16.yaml`
- `configs/sft/stage2_rank/rank32.yaml`
- `configs/sft/stage2_rank/rank64.yaml`

### Run summaries

- `outputs/sft_stage2_rank8/run_summary.json`
- `outputs/sft_stage2_rank16/run_summary.json`
- `outputs/sft_stage2_rank32/run_summary.json`
- `outputs/sft_stage2_rank64/run_summary.json`

## Stage 2 conclusion

The rank sweep does not show a meaningful quality improvement from
increasing rank beyond 16 under the tested conditions.

Rank 16 is therefore carried forward as the provisional rank for
Stage 3, where the next comparison will be:

**LoRA BF16 vs QLoRA NF4 using `all-linear`, r=16.**# SFT Stage 2 — LoRA Rank Sweep

## Objective

Evaluate LoRA ranks `{8, 16, 32, 64}` using the provisional Stage 1
target-module configuration `all-linear`.

Only the LoRA rank changes between runs.

## Fixed configuration

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Target modules: `all-linear`
- Quantization: QLoRA NF4
- Compute dtype: BF16
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Learning rate: `5e-5`
- Maximum sequence length: `512`
- Gradient accumulation: `8`
- Training steps: `100`
- Seed: `42`
- Dataset and train/validation split: unchanged from Stage 1

## Results

| Rank | Trainable params | Trainable % | Train loss | Eval loss | Eval token accuracy | Peak VRAM | Wall time | Tokens/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 9,232,384 | 1.0283% | 3.0323 | 2.9607 | 0.4302 | 2.44 GB | 376.00 s | 282.08 |
| 16 | 18,464,768 | 2.0356% | 3.0369 | 2.9599 | **0.4311** | 2.51 GB | 424.70 s | 249.74 |
| 32 | 36,929,536 | 3.9900% | 3.0339 | **2.9591** | 0.4306 | 2.64 GB | 375.49 s | **282.56** |
| 64 | 73,859,072 | 7.6739% | 3.0432 | 2.9623 | 0.4299 | 2.97 GB | 393.73 s | 269.34 |

## Observations

Increasing the LoRA rank substantially increases the number of trainable
parameters:

- r=8 → 9.23M
- r=16 → 18.46M
- r=32 → 36.93M
- r=64 → 73.86M

The validation metrics remain very close across all four ranks.

The lowest validation loss in this experiment is obtained by r=32
(`2.9591`), while the highest validation token accuracy is obtained by
r=16 (`0.4311`).

The r=64 configuration does not improve either validation metric and
requires the largest adapter and highest peak allocated VRAM.

The measured throughput also does not improve systematically with rank.
The observed values range from approximately 249.74 to 282.56 tokens/sec.

## Provisional rank selection

For subsequent experiments, **rank 16 is retained as the practical
provisional rank**.

The reason is that r=16 achieves the highest validation token accuracy
while avoiding the substantially larger parameter and memory budgets of
r=32 and r=64. Its validation loss is also essentially indistinguishable
from r=32 in this short experiment:

- r=16: `2.9599`
- r=32: `2.9591`

The difference is only `0.0008` validation loss.

This is a provisional engineering choice, not evidence that r=16 is
universally optimal.

## Limitations

This is an exploratory rank sweep:

1. Only one seed (`42`) was evaluated.
2. Each configuration was trained for only 100 steps.
3. The validation split contains 44 examples.
4. Token-level accuracy is not a human evaluation of response quality.
5. The observed differences between ranks are very small.
6. No statistical significance test is appropriate for treating these
   four single-run results as definitive.
7. The final headline configuration still requires evaluation with
   three seeds.

## Artifacts

### Configurations

- `configs/sft/stage2_rank/rank8.yaml`
- `configs/sft/stage2_rank/rank16.yaml`
- `configs/sft/stage2_rank/rank32.yaml`
- `configs/sft/stage2_rank/rank64.yaml`

### Run summaries

- `outputs/sft_stage2_rank8/run_summary.json`
- `outputs/sft_stage2_rank16/run_summary.json`
- `outputs/sft_stage2_rank32/run_summary.json`
- `outputs/sft_stage2_rank64/run_summary.json`

## Stage 2 conclusion

The rank sweep does not show a meaningful quality improvement from
increasing rank beyond 16 under the tested conditions.

Rank 16 is therefore carried forward as the provisional rank for
Stage 3, where the next comparison will be:

**LoRA BF16 vs QLoRA NF4 using `all-linear`, r=16.**
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Learning rate: `5e-5`
- Maximum sequence length: `512`
- Gradient accumulation: `8`
- Training steps: `100`
- Seed: `42`
- Dataset and train/validation split: unchanged from Stage 1

## Results

| Rank | Trainable params | Trainable % | Train loss | Eval loss | Eval token accuracy | Peak VRAM | Wall time | Tokens/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 9,232,384 | 1.0283% | 3.0323 | 2.9607 | 0.4302 | 2.44 GB | 376.00 s | 282.08 |
| 16 | 18,464,768 | 2.0356% | 3.0369 | 2.9599 | **0.4311** | 2.51 GB | 424.70 s | 249.74 |
| 32 | 36,929,536 | 3.9900% | 3.0339 | **2.9591** | 0.4306 | 2.64 GB | 375.49 s | **282.56** |
| 64 | 73,859,072 | 7.6739% | 3.0432 | 2.9623 | 0.4299 | 2.97 GB | 393.73 s | 269.34 |

## Observations

Increasing the LoRA rank substantially increases the number of trainable
parameters:

- r=8 → 9.23M
- r=16 → 18.46M
- r=32 → 36.93M
- r=64 → 73.86M

The validation metrics remain very close across all four ranks.

The lowest validation loss in this experiment is obtained by r=32
(`2.9591`), while the highest validation token accuracy is obtained by
r=16 (`0.4311`).

The r=64 configuration does not improve either validation metric and
requires the largest adapter and highest peak allocated VRAM.

The measured throughput also does not improve systematically with rank.
The observed values range from approximately 249.74 to 282.56 tokens/sec.

## Provisional rank selection

For subsequent experiments, **rank 16 is retained as the practical
provisional rank**.

The reason is that r=16 achieves the highest validation token accuracy
while avoiding the substantially larger parameter and memory budgets of
r=32 and r=64. Its validation loss is also essentially indistinguishable
from r=32 in this short experiment:

- r=16: `2.9599`
- r=32: `2.9591`

The difference is only `0.0008` validation loss.

This is a provisional engineering choice, not evidence that r=16 is
universally optimal.

## Limitations

This is an exploratory rank sweep:

1. Only one seed (`42`) was evaluated.
2. Each configuration was trained for only 100 steps.
3. The validation split contains 44 examples.
4. Token-level accuracy is not a human evaluation of response quality.
5. The observed differences between ranks are very small.
6. No statistical significance test is appropriate for treating these
   four single-run results as definitive.
7. The final headline configuration still requires evaluation with
   three seeds.

## Artifacts

### Configurations

- `configs/sft/stage2_rank/rank8.yaml`
- `configs/sft/stage2_rank/rank16.yaml`
- `configs/sft/stage2_rank/rank32.yaml`
- `configs/sft/stage2_rank/rank64.yaml`

### Run summaries

- `outputs/sft_stage2_rank8/run_summary.json`
- `outputs/sft_stage2_rank16/run_summary.json`
- `outputs/sft_stage2_rank32/run_summary.json`
- `outputs/sft_stage2_rank64/run_summary.json`

## Stage 2 conclusion

The rank sweep does not show a meaningful quality improvement from
increasing rank beyond 16 under the tested conditions.

Rank 16 is therefore carried forward as the provisional rank for
Stage 3, where the next comparison will be:

**LoRA BF16 vs QLoRA NF4 using `all-linear`, r=16.**# SFT Stage 2 — LoRA Rank Sweep

## Objective

Evaluate LoRA ranks `{8, 16, 32, 64}` using the provisional Stage 1
target-module configuration `all-linear`.

Only the LoRA rank changes between runs.

## Fixed configuration

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Target modules: `all-linear`
- Quantization: QLoRA NF4
- Compute dtype: BF16
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Learning rate: `5e-5`
- Maximum sequence length: `512`
- Gradient accumulation: `8`
- Training steps: `100`
- Seed: `42`
- Dataset and train/validation split: unchanged from Stage 1

## Results

| Rank | Trainable params | Trainable % | Train loss | Eval loss | Eval token accuracy | Peak VRAM | Wall time | Tokens/sec |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 8 | 9,232,384 | 1.0283% | 3.0323 | 2.9607 | 0.4302 | 2.44 GB | 376.00 s | 282.08 |
| 16 | 18,464,768 | 2.0356% | 3.0369 | 2.9599 | **0.4311** | 2.51 GB | 424.70 s | 249.74 |
| 32 | 36,929,536 | 3.9900% | 3.0339 | **2.9591** | 0.4306 | 2.64 GB | 375.49 s | **282.56** |
| 64 | 73,859,072 | 7.6739% | 3.0432 | 2.9623 | 0.4299 | 2.97 GB | 393.73 s | 269.34 |

## Observations

Increasing the LoRA rank substantially increases the number of trainable
parameters:

- r=8 → 9.23M
- r=16 → 18.46M
- r=32 → 36.93M
- r=64 → 73.86M

The validation metrics remain very close across all four ranks.

The lowest validation loss in this experiment is obtained by r=32
(`2.9591`), while the highest validation token accuracy is obtained by
r=16 (`0.4311`).

The r=64 configuration does not improve either validation metric and
requires the largest adapter and highest peak allocated VRAM.

The measured throughput also does not improve systematically with rank.
The observed values range from approximately 249.74 to 282.56 tokens/sec.

## Provisional rank selection

For subsequent experiments, **rank 16 is retained as the practical
provisional rank**.

The reason is that r=16 achieves the highest validation token accuracy
while avoiding the substantially larger parameter and memory budgets of
r=32 and r=64. Its validation loss is also essentially indistinguishable
from r=32 in this short experiment:

- r=16: `2.9599`
- r=32: `2.9591`

The difference is only `0.0008` validation loss.

This is a provisional engineering choice, not evidence that r=16 is
universally optimal.

## Limitations

This is an exploratory rank sweep:

1. Only one seed (`42`) was evaluated.
2. Each configuration was trained for only 100 steps.
3. The validation split contains 44 examples.
4. Token-level accuracy is not a human evaluation of response quality.
5. The observed differences between ranks are very small.
6. No statistical significance test is appropriate for treating these
   four single-run results as definitive.
7. The final headline configuration still requires evaluation with
   three seeds.

## Artifacts

### Configurations

- `configs/sft/stage2_rank/rank8.yaml`
- `configs/sft/stage2_rank/rank16.yaml`
- `configs/sft/stage2_rank/rank32.yaml`
- `configs/sft/stage2_rank/rank64.yaml`

### Run summaries

- `outputs/sft_stage2_rank8/run_summary.json`
- `outputs/sft_stage2_rank16/run_summary.json`
- `outputs/sft_stage2_rank32/run_summary.json`
- `outputs/sft_stage2_rank64/run_summary.json`

## Stage 2 conclusion

The rank sweep does not show a meaningful quality improvement from
increasing rank beyond 16 under the tested conditions.

Rank 16 is therefore carried forward as the provisional rank for
Stage 3, where the next comparison will be:

**LoRA BF16 vs QLoRA NF4 using `all-linear`, r=16.**