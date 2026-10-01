# Track B — B3.1 DPO Configuration and Validation

## Model and SFT checkpoint

- Base model: `Qwen/Qwen2.5-1.5B-Instruct`
- Selected SFT checkpoint: `outputs/sft_stage4_data100/checkpoint-100`
- SFT method: QLoRA NF4
- LoRA rank: 16
- LoRA alpha: 32
- Seed: 42

## Preference data

- Source: `data/preference_dataset.jsonl`
- Train split: `data/preference_splits/train.jsonl`
- Evaluation split: `data/preference_splits/test.jsonl`
- Train rows: 88
- Evaluation rows: 44
- Preference validator: PASS
- Total validated preference rows: 132
- Unique IDs/triples: 132
- Categories: 11
- Script: Arabic, 132/132

## Tokenizer and chat template

The SFT and DPO pipelines use the native tokenizer chat template from:

`Qwen/Qwen2.5-1.5B-Instruct`

Tokenizer audit:

- Chat template present: YES
- Tokenizer class: `Qwen2Tokenizer`
- Template source: `tokenizer.chat_template`
- Template SHA-256:
  `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`
- Padding side: `right`
- Pad token: `<|endoftext|>`
- EOS token: `<|im_end|>`

### SFT formatting

SFT renders:

1. the complete conversation with `add_generation_prompt=False`;
2. the prompt-only conversation with `add_generation_prompt=True`.

Both are produced through `tokenizer.apply_chat_template(...)`.

### DPO formatting

DPO converts each preference example to:

- `user` → prompt
- `assistant` → chosen
- `assistant` → rejected

`DPOTrainer` receives the same tokenizer through:

`processing_class=tokenizer`

Therefore DPO uses the same native chat template as SFT.

No manual Qwen chat formatting is used.

## Reference policy

The DPO policy starts from the selected SFT adapter.

The training model is:

`QLoRA base model + selected SFT adapter`

`DPOTrainer(ref_model=None)` creates the reference adapter from the policy adapter under the installed TRL/PEFT implementation.

Verified environment:

- TRL: `1.10.0`
- PEFT: `0.20.0`
- Transformers: `5.15.0`
- PyTorch: `2.8.0+cu128`
- bitsandbytes: `0.50.1`

The reference adapter is a frozen copy of the SFT/default adapter.

Manual verification:

- Default/reference adapter tensors: 392
- Maximum parameter difference after reference creation: `0.0`
- Reference adapter trainable parameters: `0`

Thus the initial reference policy is the selected SFT policy, not the raw base model.

## DPO configuration

Beta sweep:

- `0.05`
- `0.10`
- `0.30`
- `0.50`

Common configuration:

- max length: 512
- learning rate: `5e-6`
- per-device batch size: 1
- gradient accumulation: 8
- seed: 42
- BF16: enabled
- QLoRA NF4: enabled
- evaluation every 10 steps
- 50 optimizer steps for the full sweep

## Smoke validation

A 10-step DPO smoke run with `beta=0.1` completed successfully.

Observed behavior:

- final training loss: approximately `0.595`
- reward margin increased from approximately `0` to `0.33`
- reward accuracy was predominantly `1`
- run completed successfully and produced `run_summary.json`

## Full beta sweep results

The four DPO configurations were trained for 50 optimizer steps under identical settings, with only `beta` varied.

| Beta | Final eval loss | Final eval accuracy | Final eval margin |
|---:|---:|---:|---:|
| 0.05 | 0.5193 | 95.45% | 0.405 |
| 0.10 | 0.3995 | 95.45% | 0.798 |
| 0.30 | 0.2259 | 95.45% | 2.173 |
| 0.50 | 0.1965 | 95.45% | 3.320 |

All runs reached 42/44 correct preference predictions on the held-out evaluation set.

### Evaluation trajectory

**β = 0.05**

- Step 10: loss 0.5541, accuracy 93.18%, margin 0.3155
- Step 20: loss 0.5300, accuracy 95.45%, margin 0.3776
- Step 30: loss 0.5226, accuracy 95.45%, margin 0.3963
- Step 40: loss 0.5189, accuracy 95.45%, margin 0.4057
- Step 50: loss 0.5193, accuracy 95.45%, margin 0.4048

**β = 0.10**

- Step 10: loss 0.4497, accuracy 93.18%, margin 0.6311
- Step 20: loss 0.4123, accuracy 95.45%, margin 0.7564
- Step 30: loss 0.4032, accuracy 95.45%, margin 0.7888
- Step 40: loss 0.3989, accuracy 95.45%, margin 0.8015
- Step 50: loss 0.3995, accuracy 95.45%, margin 0.7983

**β = 0.30**

- Step 10: loss 0.2675, accuracy 95.45%, margin 1.816
- Step 20: loss 0.2388, accuracy 95.45%, margin 2.071
- Step 30: loss 0.2208, accuracy 95.45%, margin 2.165
- Step 40: loss 0.2232, accuracy 95.45%, margin 2.169
- Step 50: loss 0.2259, accuracy 95.45%, margin 2.173

**β = 0.50**

- Step 10: loss 0.2288, accuracy 93.18%, margin 2.836
- Step 20: loss 0.2096, accuracy 93.18%, margin 3.211
- Step 30: loss 0.2047, accuracy 95.45%, margin 3.330
- Step 40: loss 0.2002, accuracy 95.45%, margin 3.338
- Step 50: loss 0.1965, accuracy 95.45%, margin 3.320

### Interpretation

All four beta values produced the same held-out preference accuracy: 42/44 (95.45%).

Increasing beta produced progressively larger reward margins. The final DPO loss also decreased as beta increased, but DPO losses should not be interpreted as directly comparable across different beta values because beta scales the DPO objective.

Therefore, the beta sweep demonstrates that the implementation is stable across the tested beta range and that beta controls the strength of preference separation in this experiment. Actual model-selection decisions should be based on the subsequent generation-quality evaluation rather than DPO loss alone.

## B3.1 status

All B3.1 validation requirements are satisfied:

- Preference validator: PASS
- SFT checkpoint selected: YES
- Tokenizer/template compatibility recorded: YES
- Reference strategy verified: YES
- 10-step DPO smoke: PASS

B3.1 is complete.
