# SFT Stage 1 — LoRA Target Module Sweep

## Objective

Compare LoRA target-module sets for QLoRA SFT of
`Qwen/Qwen2.5-1.5B-Instruct` on the Algerian Darija instruction dataset.

The sweep fixes:

- LoRA rank: `r=16`
- LoRA alpha: `32`
- LoRA dropout: `0.05`
- Quantization: NF4 4-bit
- Compute dtype: BF16
- Learning rate: `5e-5`
- Gradient accumulation: `8`
- Maximum sequence length: `512`
- Training steps: `100`
- Seed: `42`

Only the LoRA target modules vary.

This experiment is exploratory and is intended to identify a provisional target-module configuration for subsequent SFT work.

## Configurations

| Run | Target modules |
|---|---|
| QV | `q_proj`, `v_proj` |
| QKVO | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| All-linear | `all-linear` |

## CMD

```bash
 python train_sft_trl.py \                              
  --config configs/sft/stage1_targets/target_[TARGET-MODULE].yaml \
  --max-steps 100 \
  --output-dir outputs/sft_stage1_[TARGET-MODULE]
```
and
```bash
 python scripts/test_sft_generation.py \                
  --adapter outputs/sft_stage1_[TARGET-MODULE] \
  --output outputs/sft_stage1_[TARGET-MODULE]/sample_generations.json
```

## Results

All runs completed successfully.

| Metric | QV | QKVO | All-linear |
|---|---:|---:|---:|
| Trainable parameters | 2,179,072 | 4,358,144 | 18,464,768 |
| Trainable percentage | 0.2446% | 0.4880% | 2.0356% |
| Train loss | 3.5534 | 3.4160 | 3.0318 |
| Eval loss | 3.4140 | 3.2550 | 2.9585 |
| Eval token accuracy | 0.3852 | 0.3963 | 0.4316 |
| Peak allocated VRAM | 2.39 GB | 2.40 GB | 2.51 GB |
| Peak reserved VRAM | 3.56 GB | 3.48 GB | 3.48 GB |
| Wall time | 279.25 s | 316.18 s | 378.26 s |
| Training tokens | 105,677 | 105,677 | 105,677 |
| Approx. tokens/sec | 378.47 | 334.22 | 279.40 |

The throughput values are derived as:

`105,677 training tokens / recorded training wall time`.

They were not independently benchmarked after training.

## Observations

### QV

The QV configuration uses the smallest LoRA parameter budget.

It has:

- 2.18M trainable parameters
- 0.2446% of the reported model parameters
- 2.39 GB peak allocated VRAM
- 279.25 seconds wall time
- 378.47 approximate training tokens/sec

Its validation loss was `3.4140` and validation token accuracy was `0.3852`.

### QKVO

QKVO approximately doubles the number of trainable parameters relative to QV:

`4,358,144 / 2,179,072 = 2.0x`.

Compared with QV, QKVO produced:

- lower validation loss: `3.2550` vs `3.4140`
- higher validation token accuracy: `0.3963` vs `0.3852`
- slightly higher peak allocated VRAM: `2.40` vs `2.39 GB`
- longer wall time: `316.18` vs `279.25 s`
- lower throughput: `334.22` vs `378.47 tokens/sec`

### All-linear

The all-linear configuration substantially increases the LoRA parameter budget:

- 18.46M trainable parameters
- 2.0356% of the reported model parameters

Relative to QV, this is approximately `8.47x` more trainable parameters.

In this 100-step experiment, all-linear obtained:

- the lowest validation loss: `2.9585`
- the highest validation token accuracy: `0.4316`

Its peak allocated VRAM was `2.51 GB`, while wall time increased to `378.26 seconds`.

Its derived throughput was approximately `279.40 tokens/sec`.

## Qualitative generation check

Three fixed Algerian Darija prompts were generated greedily from each adapter.

The prompts covered:

1. triangle area
2. organizing study and rest time
3. why the sky appears blue

The generations are stored in:

- `outputs/sft_stage1_qv_smoke/sample_generations.json`
- `outputs/sft_stage1_qkvo/sample_generations.json`
- `outputs/sft_stage1_all_linear/sample_generations.json`

The samples showed factual and semantic errors across configurations. For example, some responses confused the mathematical procedure for calculating triangle area, while the sky-related responses contained incorrect statements.

These samples are therefore treated as qualitative diagnostics rather than evidence of robust generation quality.

No numerical quality score is assigned from these three examples.

## Provisional decision

For the **100-step exploratory sweep**, `all-linear` is the provisional target-module configuration for the next SFT stage.

The basis for this choice is that it produced the strongest validation metrics in this experiment:

- lowest validation loss
- highest validation token accuracy

The additional computational cost is measurable but remains modest in peak allocated VRAM on the current hardware:

- QV: `2.39 GB`
- QKVO: `2.40 GB`
- All-linear: `2.51 GB`

However, all-linear is substantially more parameter-heavy and slower than the smaller target sets.

Therefore this should be treated as a **provisional experimental choice**, not a claim that all-linear is generally superior.

## Limitations

This sweep has several important limitations:

1. Only one random seed (`42`) was evaluated.
2. Each configuration was trained for only `100` steps.
3. The validation split contains only `44` examples.
4. Token-level accuracy is not equivalent to human evaluation of Darija response quality.
5. Only three fixed prompts were used for qualitative generation inspection.
6. The qualitative generations contained errors across configurations.
7. The throughput values are derived from recorded token counts and wall times rather than from a dedicated throughput benchmark.
8. The comparison does not establish generalization to unseen Darija tasks or domains.
9. The experiment does not test different LoRA ranks, learning rates, or other SFT hyperparameters.

Consequently, the results should be interpreted as a target-module screening experiment rather than a final hyperparameter conclusion.

## Artifacts

### Configurations

- `configs/sft/stage1_targets/target_qv.yaml`
- `configs/sft/stage1_targets/target_qkvo.yaml`
- `configs/sft/stage1_targets/target_all_linear.yaml`

### Run summaries

- `outputs/sft_stage1_qv_smoke/run_summary.json`
- `outputs/sft_stage1_qkvo/run_summary.json`
- `outputs/sft_stage1_all_linear/run_summary.json`

### Generation samples

- `outputs/sft_stage1_qv_smoke/sample_generations.json`
- `outputs/sft_stage1_qkvo/sample_generations.json`
- `outputs/sft_stage1_all_linear/sample_generations.json`

## Conclusion

The Stage 1 target-module sweep shows a clear quality/cost trade-off under the tested 100-step setting.

QV provides the smallest and fastest configuration. QKVO improves the validation metrics with roughly twice the trainable parameters. All-linear obtains the strongest validation metrics in this experiment, at the cost of a substantially larger adapter and lower throughput.

`all-linear` is therefore carried forward as the provisional target-module configuration for the next experiment, subject to validation in a longer SFT run.