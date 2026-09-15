# TRL SFT Smoke Test

## Status

**PASS**

This report documents the SFT pipeline validation for DziriDPO.

The purpose of this experiment was to verify that the complete TRL SFT pipeline correctly formats the Algerian Darija instruction data, applies response-only supervision, trains a QLoRA adapter without numerical or memory failures, saves the adapter, and successfully reloads it for generation.

This was a **pipeline smoke test**, not a model-quality or convergence experiment.

---

## 1. Objective

validates the following SFT pipeline:

```text
Reviewed Darija instruction data
        ↓
Qwen chat template
        ↓
Explicit tokenization
        ↓
Response-only labels
        ↓
4-bit QLoRA
        ↓
TRL SFTTrainer
        ↓
Adapter checkpoint
        ↓
Reload
        ↓
Generation
```

The main failure modes targeted were:

* incorrect chat-template formatting;
* prompt tokens accidentally contributing to the loss;
* inconsistent prompt/response token boundaries;
* TRL modifying already-validated labels;
* LoRA/QLoRA training failures;
* GPU memory exhaustion;
* invalid or unusable adapter checkpoints.

---

## 2. Dataset

The Track B reviewed dataset contains **220 accepted instruction examples**.

The dataset was split using seed `42` with stratification by category:

| Split      | Examples |      Categories |
| ---------- | -------: | --------------: |
| Train      |      176 | 16 per category |
| Validation |       44 |  4 per category |

There are 11 categories:

* education
* daily_life
* general_qa
* reasoning
* algerian_culture
* commerce
* translation
* code_switching
* technical
* safety
* humor

The source dataset is:

```text
data/instruction_dataset_v1.jsonl
```

The split datasets are:

```text
data/splits/train.jsonl
data/splits/val.jsonl
```

---

## 3. Chat Formatting

The model used for Track B is:

```text
Qwen/Qwen2.5-1.5B-Instruct
```

The tokenizer's native chat template was used rather than manually reproducing the Qwen ChatML format.

The complete conversation was rendered with:

```python
tokenizer.apply_chat_template(
    messages,
    tokenize=False,
    add_generation_prompt=False,
)
```

The prompt portion was rendered separately with:

```python
tokenizer.apply_chat_template(
    messages[:-1],
    tokenize=False,
    add_generation_prompt=True,
)
```

Both strings were then explicitly tokenized with:

```python
tokenizer(
    text,
    add_special_tokens=False,
)
```

This explicit tokenization was used because `tokenize=True` in the installed Transformers environment produced unexpected behavior during the initial tokenizer audit.

For each example, the implementation verifies:

```text
tokenized_prompt == tokenized_full_conversation[:prompt_length]
```

before constructing labels.

---

## 4. Response-Only Supervision

The SFT formatter constructs labels as:

```text
prompt tokens   → -100
assistant tokens → original token IDs
```

Therefore, prompt tokens do not contribute to the cross-entropy loss.

The formatter also verifies that:

* the final message is an assistant message;
* the assistant response contains tokens;
* the prompt is an exact prefix of the full conversation;
* truncation does not remove the entire response.

The resulting fields are:

```text
input_ids
attention_mask
labels
```

A dataset-wide formatting audit was performed before training.

### Formatting audit

```text
TRAIN
Examples:          176
Truncated:           0
Min response:       12 tokens
Max response:      128 tokens

VALIDATION
Examples:           44
Truncated:           0
Min response:       11 tokens
Max response:      115 tokens
```

Thus all 220 examples contained supervised response tokens and none required truncation at `max_length=512`.

---

## 5. TRL Integration

The installed versions were:

```text
trl             1.10.0
transformers    5.15.0
peft            0.20.0
bitsandbytes    0.50.1
torch           2.8.0+cu128
```

The TRL `SFTTrainer` implementation was inspected to verify its behavior with pre-tokenized datasets.

Because the dataset already contains `input_ids`, TRL recognizes it as processed.

Because the dataset already contains `labels`, TRL does not regenerate them.

The trainer was therefore configured with:

```python
dataset_kwargs={
    "skip_prepare_dataset": True,
}
```

This prevents TRL from reapplying chat formatting or truncation to the already-validated examples.

A custom data collator was used to preserve the explicit labels:

```text
input_ids       → pad_token_id
attention_mask  → 0
labels          → -100
```

The Qwen tokenizer configuration was verified as:

```text
pad_token     = <|endoftext|>
pad_token_id  = 151643

eos_token     = <|im_end|>
eos_token_id  = 151645
```

---

## 6. Training Configuration

The smoke run used:

```text
Base model:
Qwen/Qwen2.5-1.5B-Instruct

Quantization:
4-bit NF4
double quantization enabled
BF16 compute

LoRA:
rank              = 16
alpha             = 32
dropout           = 0.05
target modules    = q_proj, k_proj, v_proj, o_proj

Sequence length:
512

Batch size:
1

Gradient accumulation:
8

Effective batch size:
8

Learning rate:
5e-5

Gradient clipping:
1.0

Gradient checkpointing:
enabled

Training steps:
20

Seed:
42
```

The user's RTX 3050 supports BF16, so BF16 was used rather than FP16.

---

## 7. Smoke Training Results

The 20-step run completed successfully.

Representative training logs:

```text
step 1:
loss = 3.694
grad_norm = 1.555

step 10:
loss = 3.703
grad_norm = 1.352

step 18:
loss = 3.319
grad_norm = 1.148

step 20:
loss = 3.614
grad_norm = 1.477
```

The evaluation result at the end of the smoke run was:

```text
eval_loss             = 3.571
eval_mean_token_accuracy = 0.3722
```

The complete training run reported:

```text
train_runtime        = 61.96 s
train_loss           = 3.695
train_samples/sec    = 2.582
train_steps/sec      = 0.323
peak VRAM             = 2.50 GB
```

Gradient norms remained finite throughout the run and no NaN, exploding-gradient, or out-of-memory failure occurred.

### Interpretation

The smoke loss should **not** be interpreted as evidence of successful SFT convergence.

Twenty optimizer steps are insufficient for a meaningful model-quality conclusion, particularly with only 176 training examples and heterogeneous categories.

The relevant conclusion is that the training pipeline is operational and produces valid gradients and evaluation outputs.

---

## 8. Batch-Level Label Audit

Before training, a two-example batch was inspected:

```text
input_ids:       (2, 177)
labels:          (2, 177)
attention_mask:  (2, 177)

Supervised tokens: 205
Masked tokens:     149
```

This confirms that the collator preserved the response-only label structure after padding.

No prompt tokens were unintentionally converted into supervised labels.

---

## 9. Checkpoint Save and Reload

The smoke adapter was saved to:

```text
outputs/sft_smoke
```

The checkpoint was subsequently reloaded using:

```text
Qwen/Qwen2.5-1.5B-Instruct
        +
outputs/sft_smoke
```

The reload test passed.

The base model loaded successfully in the same 4-bit NF4/BF16 configuration and the LoRA adapter was successfully attached with PEFT.

Therefore:

```text
checkpoint save       PASS
base-model reload     PASS
adapter reload        PASS
```

---

## 10. Generation Sanity Check

Generation was tested using the reloaded adapter on three prompts.

### Test 1

```text
تقدر تشرحلي كيفاش نحسبو مساحة المثلث؟
```

The model produced a mathematically plausible explanation, although it was predominantly MSA rather than Algerian Darija and the response was incomplete.

### Test 2

```text
واش نقدر ندير باش ننظم وقتي بين القراية والراحة؟
```

The model produced a coherent general answer, again with substantial MSA usage.

### Test 3

```text
علاش السماء تبان زرقاء؟
```

The model produced an inappropriate refusal:

```text
عذراً، لا أستطيع مساعدتك في هذا.
```

### Interpretation

These outputs demonstrate that the reloaded adapter can generate normally, but they should **not** be treated as evidence of SFT quality.

The MSA-heavy responses and inappropriate refusal are plausible outcomes from an extremely short 20-step smoke run.

No qualitative optimization was performed based on these samples because doing so would compromise the baseline experiment.

---

## 11. Resource Usage

Peak allocated GPU memory during the smoke run was:

```text
2.50 GB
```

This remained comfortably below the available 4 GB VRAM of the RTX 3050 Laptop GPU.

The run completed without an out-of-memory error.

---

## 12. Validation Checklist

| Requirement                       | Result |
| --------------------------------- | ------ |
| SFT formatting implemented        | PASS   |
| Native Qwen chat template used    | PASS   |
| Prompt/response boundary verified | PASS   |
| Response-only labels verified     | PASS   |
| Dataset-wide audit                | PASS   |
| No truncation at 512 tokens       | PASS   |
| TRL SFT integration               | PASS   |
| Pre-tokenized dataset preserved   | PASS   |
| Custom label-preserving collator  | PASS   |
| 4-bit QLoRA                       | PASS   |
| BF16 training                     | PASS   |
| Gradient flow                     | PASS   |
| Smoke loss/evaluation             | PASS   |
| Peak VRAM logged                  | PASS   |
| Adapter checkpoint saved          | PASS   |
| Adapter reload                    | PASS   |
| Generation after reload           | PASS   |

---

## 13. Conclusion

**B2.1 is complete.**

The Track B SFT pipeline has been validated end-to-end:

```text
reviewed data
    ↓
Qwen chat template
    ↓
explicit tokenization
    ↓
response-only labels
    ↓
pre-tokenized Dataset
    ↓
custom padding collator
    ↓
TRL SFTTrainer
    ↓
4-bit QLoRA + BF16
    ↓
adapter checkpoint
    ↓
successful reload
    ↓
successful generation
```

The smoke experiment validates **pipeline correctness**, not final SFT quality.

The next stage should therefore use the validated pipeline for the actual SFT baseline rather than modifying the smoke configuration based on its qualitative outputs.

## 14. Reproduction Commands

### 14.1 Compile-check the training script

```bash
python -m py_compile scripts/train_sft_trl.py
```

### 14.2 Run the B2.1 smoke experiment

The actual smoke run used 20 optimizer steps:

```bash
python scripts/train_sft_trl.py \
    --config configs/sft_baseline.yaml \
    --max-steps 20 \
    --output-dir outputs/sft_smoke
```

### 14.3 Adapter reload test

The saved adapter was reloaded from:

```text
outputs/sft_smoke
```

The reload test verified that the base Qwen model and LoRA adapter could be loaded successfully.

### 14.4 Generation sanity test

Generation was then tested using the reloaded adapter:

```bash
python scripts/test_sft_generation.py \
    --adapter outputs/sft_smoke
```

### 14.5 Smoke-test artifacts

The main output directory was:

```text
outputs/sft_smoke/
```

This directory contains the trained LoRA adapter/checkpoint produced by the 20-step smoke run.

### 14.6 Actual experiment identity

For future reference:

```text
Experiment: B2.1 SFT smoke test
Config:     configs/sft_baseline.yaml
Steps:      20
Output:     outputs/sft_smoke
Seed:       42
Model:      Qwen/Qwen2.5-1.5B-Instruct
Method:     4-bit QLoRA + BF16
Max length: 512
```

**Important:** `outputs/sft_smoke` is a smoke-test checkpoint and must not be treated as the final SFT baseline or used for quality conclusions.
