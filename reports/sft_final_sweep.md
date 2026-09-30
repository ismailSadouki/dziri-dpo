# Final SFT Sweep

## Final configuration

- Model: Qwen/Qwen2.5-1.5B-Instruct
- Method: QLoRA NF4
- LoRA rank: 16
- LoRA target modules: all-linear
- LoRA alpha: 32
- LoRA dropout: 0.05
- Training data: 176 examples (100%)
- Validation data: 44 examples
- Max length: 512
- Learning rate: 5e-5
- Gradient accumulation: 8
- Training steps: 100

## Three-seed validation

| Seed | Eval loss | Eval token accuracy | Peak VRAM (GB) |
|---:|---:|---:|---:|
| 42 | 2.9739 | 0.4282 | 2.51 |
| 43 | 2.9642 | 0.4279 | 2.51 |
| 44 | 2.9692 | 0.4289 | 2.51 |
| Mean ± SD | 2.9691 ± 0.0049 | 0.4283 ± 0.0005 | 2.51 ± 0.0004 |

## Selection

The selected SFT checkpoint for subsequent DPO experiments is:

`outputs/sft_stage4_data100/checkpoint-100`

This is the seed-42 run, selected as the predetermined baseline configuration rather than by selecting the best-performing seed after observing the results.

## Sweep conclusions

### Target modules

The Stage 1 exploratory sweep compared q,v; q,k,v,o; and all-linear targets. All-linear achieved the lowest validation loss and highest validation token accuracy in the 100-step exploratory run, at the cost of additional trainable parameters and runtime.

### LoRA rank

The Stage 2 exploratory rank sweep compared ranks 8, 16, 32, and 64. Rank 32 had the lowest validation loss, while rank 16 had the highest token accuracy. Differences were small, while rank 64 increased parameter count and VRAM without improving validation metrics. Rank 16 was carried forward as the practical baseline.

### LoRA vs QLoRA

Full BF16 LoRA did not complete training on the available GPU because the first training step exceeded available VRAM. QLoRA NF4 completed successfully. Therefore this comparison establishes hardware feasibility for the current setup rather than demonstrating an intrinsic quality advantage of QLoRA.

### Data fraction

Using nested deterministic subsets of the 176-example training set, validation performance improved as training data increased from 25% to 50% to 100% in the fixed 100-step experiment.

### Tokenizer fertility

Not performed. This analysis was considered ancillary to the SFT/DPO pipeline and no directly matched bilingual corpus was available for a clean comparison.

## Limitations

- Experiments use a 44-example validation set.
- Exploratory sweeps use a single seed.
- Training was limited to 100 steps.
- Evaluation uses token-level accuracy and loss; these are not human-quality measures.
- The three-seed replication supports stability of the selected configuration but does not establish broad generalization.
- The selected checkpoint is a research baseline for the subsequent DPO experiment, not a claim of optimal SFT quality.
