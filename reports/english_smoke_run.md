# M4.2 — English Smoke Run and Held-Out Preference Evaluation

## 1. Experiment Overview

### Objective

validates the complete scratch DPO training pipeline on a small English preference dataset before moving to the Algerian Darija alignment pipeline.

The purpose of this experiment is **pipeline validation**, not achieving state-of-the-art preference-learning performance.

The experiment evaluates whether:

1. the scratch DPO training loop executes correctly;
2. policy and reference log-probabilities are computed correctly;
3. gradients reach the LoRA parameters;
4. checkpoints can be saved and loaded;
5. training can be resumed;
6. held-out preference evaluation works independently of the training loop;
7. the trained policy shows evidence of learning the preference signal;
8. generation remains qualitatively stable after DPO training.

A key principle for this experiment is that **successful execution is not equivalent to successful preference learning**. The run must therefore be evaluated using both engineering and learning criteria.

---

## 2. Experiment Status

| Component                       | Status                                             |
| ------------------------------- | -------------------------------------------------- |
| Scratch DPO training loop       | PASS                                               |
| Forward/reference computation   | PASS                                               |
| Gradient computation            | PASS                                               |
| LoRA-only optimization          | PASS                                               |
| 50-step training run            | PASS                                               |
| Checkpoint-25                   | SAVED                                              |
| Checkpoint-50                   | SAVED                                              |
| Checkpoint reload               | PASS                                               |
| Held-out evaluation pipeline    | PASS                                               |
| Held-out preference improvement | NOT DEMONSTRATED                                   |
| Generation sanity               | PASS                                               |
| Catastrophic degeneration       | NOT OBSERVED                                       |
| Overall M4.2                    | **PARTIAL / LEARNING VALIDATION NOT DEMONSTRATED** |

The run successfully exercised the complete pipeline, but the 50-step experiment did **not** produce convincing evidence that the policy learned to prefer the chosen responses on the held-out set.

This should not be interpreted as evidence that the DPO implementation is incorrect.

---

# 3. Model and Training Configuration

## 3.1 Base Model

Model:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

The model was loaded using 4-bit quantization.

### Quantization

```text
load_in_4bit: true
quantization type: NF4
double quantization: true
compute dtype: bfloat16
```

The effective architecture used for training was:

```text
Qwen base model
        |
        +-- LoRA enabled --> policy πθ
        |
        +-- LoRA disabled -> reference πref
```

The reference policy therefore uses the same underlying quantized base model while disabling the trainable LoRA adapter.

---

## 3.2 LoRA Configuration

```text
rank r:             16
alpha:              32
dropout:            0.05
bias:               none
target modules:
    q_proj
    k_proj
    v_proj
    o_proj
```

Parameter counts observed during the run:

```text
Total parameters:      496,195,456
Trainable parameters:    2,162,688
Trainable percentage:        0.4359%
```

Only the LoRA parameters were optimized.

---

## 3.3 DPO Configuration

```text
β:                    0.1
learning rate:        5.0e-5
weight decay:         0.0
max gradient norm:    1.0
maximum sequence length: 512
```

Training:

```text
batch size:                    1
gradient accumulation steps:  2
maximum optimization steps:   50
seed:                          42
```

The small batch size was primarily constrained by the available GPU memory.

---

# 4. DPO Objective

Each preference example consists of:

$$
(x,y_w,y_l)
$$

where:

* \(x\) is the prompt;
* \(y_w\) is the chosen response;
* \(y_l\) is the rejected response.

For each response, the policy/reference log-ratio is:

$$
r_w =
\log\pi_\theta(y_w|x)
-
\log\pi_{\mathrm{ref}}(y_w|x)
$$

$$
r_l =
\log\pi_\theta(y_l|x)
-
\log\pi_{\mathrm{ref}}(y_l|x)
$$

The DPO margin is:

$$
\Delta = r_w-r_l
$$

equivalently,

$$
\Delta =
\left[
\log\pi_\theta(y_w|x)
-
\log\pi_\theta(y_l|x)
\right]
-
\left[
\log\pi_{\mathrm{ref}}(y_w|x)
-
\log\pi_{\mathrm{ref}}(y_l|x)
\right].
$$

The loss is:

$$
\mathcal L_{\mathrm{DPO}}
=
-\log\sigma(\beta\Delta).
$$

The sequence-level rewards reported by the implementation are:

$$
R_w=\beta
\left[
\log\pi_\theta(y_w|x)
-
\log\pi_{\mathrm{ref}}(y_w|x)
\right]
$$

and

$$
R_l=\beta
\left[
\log\pi_\theta(y_l|x)
-
\log\pi_{\mathrm{ref}}(y_l|x)
\right].
$$

Therefore:

$$
R_w-R_l=\beta\Delta.
$$

---

# 5. Reference Policy Strategy

The reference policy is not a separately trained model.

The same quantized base model is used with the LoRA adapter disabled:

```text
                         Qwen base
                            |
                 +----------+----------+
                 |                     |
            LoRA enabled          LoRA disabled
                 |                     |
             πθ policy             πref
                 |                     |
              gradients             no grad
```

Reference computation is performed under:

```python
torch.no_grad()
model.disable_adapter()
```

The resulting reference log-probabilities are detached and do not participate in gradient computation.

This design was already validated before.

---

# 6. Dataset

## 6.1 Source

The English preference data comes from:

```text
Anthropic/hh-rlhf
subset: helpful-base
```

The source examples were converted into canonical preference triples:

```text
{
    "id": ...,
    "prompt": ...,
    "chosen": ...,
    "rejected": ...,
    "source": "Anthropic/hh-rlhf",
    "split": "train",
    "metadata": ...
}
```

The final training/evaluation setup used:

```text
Training examples: 1736
Evaluation examples: 200
Maximum sequence length: 512
Seed: 42
```

The original candidate training pool contained 1800 examples. Examples with prompts exceeding the 512-token prompt constraint were filtered.

The resulting training file therefore contains:

```text
1736 training examples
```

The held-out evaluation file contains:

```text
200 evaluation examples
```

The evaluation set was separately checked with the preference-data validator and all 200 examples passed validation.

---

# 7. Sequence-Length Policy

The scratch implementation deliberately forbids truncating the prompt itself.

The prompt is first tokenized using the Qwen chat template with:

```text
add_generation_prompt=True
```

If:

$$
|prompt| \geq 512
$$

the example is rejected rather than silently truncating the conversational context.

This resulted in filtering a small fraction of the original 1800-example training pool.

A prompt-length audit of the original 1800 examples showed:

```text
Mean:       175.2 tokens
Median:     131.0 tokens
P95:        465 tokens
P99:        707 tokens
Maximum:  1697 tokens

> 512:       62 examples
> 640:       26 examples
> 768:       13 examples
> 896:        6 examples
> 1024:       4 examples
> 1280:       3 examples
> 1536:       2 examples
```

A 1024-token experiment was previously attempted, but it produced a GPU memory failure during the vocabulary-sized `log_softmax` operation.

For a vocabulary of approximately 152k tokens, the concatenated DPO forward pass creates a large temporary tensor:

$$
[2B,T,V].
$$

With \(B=1\), \(T\approx1024\), and \(V\approx151936\), this is already large enough to create significant memory pressure on the available GPU.

Therefore:

```text
MAX_LENGTH = 512
```

was retained for the smoke experiment.

---

# 8. Training Execution

The full 50-step run completed successfully.

The training produced:

```text
checkpoint-25
checkpoint-50
```

No out-of-memory error occurred during the 512-token run.

The training loop produced finite losses and nonzero gradient norms throughout the observed run.

---

# 9. Training Trajectory

The first optimization step starts close to the DPO neutral point:

```text
step 1
loss       = 0.6931
reward_acc = 0.000
margin     = 0.0000
grad_norm  = 14.7316
```

The initial loss:

$$
-\log\sigma(0)=\log 2\approx0.6931
$$

is the expected neutral DPO loss when the policy and reference produce equal preference margins.

The following steps showed movement away from this initial state.

Representative values:

| Step |   Loss | Reward accuracy |  Margin |
| ---: | -----: | --------------: | ------: |
|    1 | 0.6931 |           0.000 |  0.0000 |
|    2 | 0.6763 |           1.000 |  0.3404 |
|    3 | 0.6691 |           1.000 |  0.4864 |
|    4 | 0.6168 |           1.000 |  1.5908 |
|    6 | 0.8128 |           0.000 | -2.2648 |
|   10 | 0.6442 |           1.000 |  1.0049 |
|   11 | 0.5519 |           1.000 |  3.0583 |
|   16 | 0.8163 |           0.000 | -2.3275 |
|   19 | 0.5874 |           1.000 |  2.2396 |
|   25 | 0.5803 |           1.000 |  2.4000 |
|   26 | 0.9198 |           0.000 | -4.1123 |
|   29 | 0.9330 |           0.000 | -4.3314 |
|   35 | 0.5930 |           1.000 |  2.1144 |
|   42 | 0.4625 |           1.000 |  5.3100 |
|   47 | 0.5114 |           1.000 |  4.0400 |
|   50 | 0.5541 |           1.000 |  3.0057 |

Because the batch size is one, the per-step reward accuracy is necessarily binary:

```text
0.0 or 1.0
```

It should therefore **not** be interpreted as a smooth training curve.

The margins also fluctuate substantially between individual examples.

For example:

```text
step 25: margin = +2.4000
step 26: margin = -4.1123
step 29: margin = -4.3314
step 42: margin = +5.3100
step 50: margin = +3.0057
```

This behavior is consistent with a highly noisy small-batch smoke run.

---

# 10. Held-Out Preference Evaluation

A separate evaluator was implemented in:

```text
eval/preference_accuracy.py
```

It loads the trained adapter independently and computes the same DPO preference margin:

$$
\Delta =
(\log\pi_\theta(y_w|x)-\log\pi_\theta(y_l|x))
-
(\log\pi_{\mathrm{ref}}(y_w|x)-\log\pi_{\mathrm{ref}}(y_l|x)).
$$

A prediction is considered correct when:

$$
\Delta>0.
$$

Evaluation was performed on:

```text
200 held-out examples
```

using:

```text
batch size = 1
max length = 512
```

---

# 11. Held-Out Results

## Step 0

At initialization, the policy and reference are identical because the LoRA adapter has not yet learned anything.

Therefore:

$$
\Delta=0
$$

for all examples, up to numerical precision.

Results:

```text
examples:              200
preference accuracy:   0.0000
non-tie accuracy:      N/A
ties:                  200
tie rate:              1.0000

mean margin:           0.0000
median margin:         0.0000

mean chosen reward:    0.0000
mean rejected reward:  0.0000
```

The 0% strict accuracy is therefore **not a failure**. It is an artifact of defining correctness as strictly:

```text
margin > 0
```

when every initial margin is exactly tied.

---

## Step 25

```text
examples:              200

preference accuracy:   0.3950
non-tie accuracy:      0.4675
ties:                  31
tie rate:              0.1550

mean margin:          -0.0059375
median margin:         0.0000

mean chosen reward:    0.1930963
mean rejected reward:  0.1949072
```

There were:

```text
169 non-tied examples
79 correct non-tied predictions
```

giving:

$$
79/169\approx46.75\%.
$$

The average chosen reward was slightly lower than the average rejected reward:

$$
0.1931 < 0.1949.
$$

The mean preference margin was also slightly negative:

$$
\bar{\Delta}\approx-0.0059.
$$

---

## Step 50

```text
examples:              200

preference accuracy:   0.4100
non-tie accuracy:      0.4713
ties:                  26
tie rate:              0.1300

mean margin:          -0.05375
median margin:         0.0000

mean chosen reward:    0.2729315
mean rejected reward:  0.2763309
```

There were:

```text
174 non-tied examples
82 correct non-tied predictions
```

giving:

$$
82/174\approx47.13\%.
$$

The average rewards increased for both responses:

```text
chosen reward:   0.1931 -> 0.2729
rejected reward: 0.1949 -> 0.2763
```

However, the rejected reward remained slightly higher.

The final mean margin was:

$$
\bar{\Delta}\approx-0.0538.
$$

---

# 12. Held-Out Evaluation Summary

| Checkpoint |  Accuracy | Non-tie accuracy | Tie rate | Mean margin | Chosen reward | Rejected reward |
| ---------- | --------: | ---------------: | -------: | ----------: | ------------: | --------------: |
| Step 0     |      0.0% |              N/A |   100.0% |      0.0000 |        0.0000 |          0.0000 |
| Step 25    |     39.5% |           46.75% |    15.5% |     -0.0059 |        0.1931 |          0.1949 |
| Step 50    | **41.0%** |       **47.13%** |    13.0% | **-0.0538** |        0.2729 |          0.2763 |

The step-50 checkpoint is numerically the best of the two trained checkpoints according to both:

```text
strict preference accuracy
non-tie preference accuracy
```

However, neither checkpoint exceeds 50% preference accuracy.

More importantly, the mean reward gap is still unfavorable:

$$
\bar R_w-\bar R_l < 0.
$$

Therefore the run does **not** provide convincing evidence that DPO has learned the desired preference direction on the held-out set.

---

# 13. Interpretation of the Evaluation

The result should be interpreted carefully.

## What the result demonstrates

The run demonstrates that:

* the DPO loss is executable;
* policy gradients are produced;
* LoRA parameters update;
* the reference path remains non-gradient;
* checkpoints can be saved;
* checkpoints can be reloaded;
* the evaluator can independently load checkpoints;
* preference margins move away from the initial neutral state;
* the trained model can still generate coherent text.

## What the result does not demonstrate

The experiment does **not** demonstrate that:

```text
DPO successfully learned the HH-RLHF preference signal.
```

The held-out accuracy remains below chance-like 50% among non-ties:

```text
checkpoint-25: 46.75%
checkpoint-50: 47.13%
```

and the mean reward difference remains slightly unfavorable.

Therefore, the correct conclusion is not:

> "DPO failed."

Nor is it:

> "DPO succeeded."

The correct conclusion is:

> **The scratch DPO pipeline executes successfully, but this short 50-step smoke run does not demonstrate held-out preference learning.**

This is an important distinction because the experiment was deliberately designed as a small smoke test rather than a properly tuned DPO training run.

---

# 14. Tie Analysis

Tie handling is important because the policy starts identical to the reference.

At step 0:

```text
200 / 200 examples tied
tie rate = 100%
```

At step 25:

```text
31 / 200 tied
tie rate = 15.5%
```

At step 50:

```text
26 / 200 tied
tie rate = 13.0%
```

Thus training clearly moved many examples away from the initial policy/reference equality.

However, moving away from zero does not necessarily mean moving in the correct direction.

This is why both:

```text
tie rate
```

and:

```text
preference accuracy among non-ties
```

are reported.

---

# 15. Reward Analysis

At step 25:

$$
\bar R_w=0.1931
$$

$$
\bar R_l=0.1949
$$

so:

$$
\bar R_w-\bar R_l\approx-0.0018.
$$

At step 50:

$$
\bar R_w=0.2729
$$

$$
\bar R_l=0.2763
$$

so:

$$
\bar R_w-\bar R_l\approx-0.0034.
$$

The absolute reward magnitude increased during training, but the relative ordering did not improve.

This is an important diagnostic:

> The policy is moving relative to the reference, but the movement is not consistently favoring the chosen responses.

Consequently, raw reward growth should not be interpreted as successful DPO learning.

---

# 16. Margin Analysis

The DPO margin is the central preference-learning quantity:

$$
\Delta
=
(r_w-r_l).
$$

Positive:

$$
\Delta>0
$$

means the policy has shifted relatively more toward the chosen response.

Negative:

$$
\Delta<0
$$

means the policy has shifted relatively more toward the rejected response.

The held-out mean margin changed from:

```text
step 0:   0.0000
step 25: -0.0059
step 50: -0.0538
```

This is not the desired direction.

The median remains exactly:

```text
0.0000
```

because a substantial fraction of examples remain tied.

The training run therefore shows movement in the DPO margin but not convincing movement in the correct direction on held-out data.

---

# 17. KL / Reference-Distance Diagnostics

The training loop records:

```text
chosen_kl_proxy
rejected_kl_proxy
```

These values are computed from sequence-level policy/reference log-ratio quantities.

They should **not** be described as exact token-level KL divergence.

The current diagnostic should therefore be interpreted as:

> a sequence-level proxy for how the policy's log-probability of the response changes relative to the reference.

It is useful for detecting extreme movement away from the reference, but it is not equivalent to:

$$
D_{\mathrm{KL}}(\pi_\theta\|\pi_{\mathrm{ref}})
$$

over the full vocabulary distribution.

This distinction is retained deliberately in the experiment documentation.

No evidence from the observed run indicated catastrophic policy movement or numerical instability.

---

# 18. Response-Length Diagnostics

The training loop records:

```text
chosen_length
rejected_length
```

in order to detect length drift.

Length matters in DPO because sequence-level log-probability sums are sensitive to the number of response tokens.

A model can therefore appear to change preference behavior partly through response-length effects rather than purely through semantic preference alignment.

For this smoke run, no qualitative evidence of pathological length behavior or degeneration was observed in the generated samples.

A more rigorous statistical length-drift analysis should be performed from the complete `metrics.jsonl` history before making a quantitative claim about length distributions.

---

# 19. Generation Evaluation

Fixed-seed generation was performed at:

```text
step 0
step 25
step 50
```

using the same evaluation prompts and generation configuration.

Generation settings:

```text
seed:           42
temperature:    0.7
top_p:          0.9
max_new_tokens: 128
```

Eight fixed prompts were used, covering topics such as:

* regularization and overfitting;
* correlation versus causation;
* dataset quality;
* gradient descent;
* validation sets;
* train/test generalization;
* confidence intervals;
* normalization.

The purpose was not to measure factuality statistically, but to detect obvious qualitative degeneration.

---

# 20. Generation Findings

The generated outputs at steps 0, 25, and 50 remained broadly coherent.

Observed behavior:

* no obvious catastrophic repetition;
* no obvious infinite-generation behavior;
* no major formatting collapse;
* no obvious collapse into a single repeated phrase;
* general response style remained similar;
* response lengths remained broadly reasonable.

However, there was also **no convincing qualitative improvement** in answer quality across the checkpoints.

Some factual weaknesses were already present at step 0.

Examples included:

* an incorrect or confused explanation of correlation;
* a weak explanation of gradient descent;
* confusion between validation and test sets;
* an inaccurate explanation of confidence intervals;
* an incorrect description of normalization.

Some later generations became more convoluted or introduced questionable claims rather than clearly improving these weaknesses.

Therefore:

> **The generation test passes as a degeneration sanity check, but it does not provide evidence of meaningful quality improvement.**

---

# 21. Degeneration Assessment

| Property                               | Assessment                 |
| -------------------------------------- | -------------------------- |
| Repetition collapse                    | Not observed               |
| Infinite/repeated generation           | Not observed               |
| Formatting collapse                    | Not observed               |
| Major fluency collapse                 | Not observed               |
| Severe response-length explosion       | Not observed qualitatively |
| Clear factual improvement              | Not observed               |
| Clear preference-alignment improvement | Not observed               |

The model therefore survived the smoke run without an obvious catastrophic generation failure.

---

# 22. Checkpoints

Two checkpoints were saved:

```text
outputs/dpo_english_m4_2/checkpoint-25
outputs/dpo_english_m4_2/checkpoint-50
```

The checkpoint structure includes the LoRA adapter and training state required by the scratch training workflow.

The step-50 checkpoint is the strongest candidate among the available checkpoints because:

```text
strict accuracy:
39.5% -> 41.0%

non-tie accuracy:
46.75% -> 47.13%

tie rate:
15.5% -> 13.0%
```

Nevertheless, it should **not** be described as a successful DPO checkpoint because the held-out preference accuracy remains below 50% and the mean reward gap remains negative.

For this reason, the checkpoint is best described as:

> **best observed smoke-run checkpoint**

rather than:

> **successful DPO checkpoint**.

---

# 23. Engineering Validation

The following engineering properties were validated during M4.2:

### Training execution

```text
50 optimization steps completed
```

### Gradients

Gradient norms were nonzero throughout the run.

Representative values:

```text
step 1:  14.7316
step 10: 20.1197
step 25: 16.2127
step 42:  9.4219
step 50: 12.4925
```

This confirms that the LoRA parameters received gradients and the optimizer was operating.

### Numerical stability

No NaN/Inf loss or training crash was observed.

### Memory

The 512-token configuration completed successfully.

The previously tested 1024-token configuration produced a GPU memory failure during the large vocabulary log-softmax operation, motivating the 512-token constraint.

### Checkpointing

Both checkpoint-25 and checkpoint-50 were successfully saved.

### Evaluation

The saved adapters were independently loaded by the held-out evaluator.

### Generation

The saved checkpoints could be loaded for generation.

---

# 24. Known Warnings

The run produced the following non-blocking warnings.

## Hugging Face authentication

The Hugging Face Hub reported unauthenticated requests.

This does not affect the correctness of the experiment because the required public model/dataset resources were accessible.

## Gradient checkpointing warning

PyTorch emitted a warning concerning the `use_reentrant` argument for checkpointing.

This did not prevent training.

## Gradient checkpointing input warning

The following warning appeared:

```text
None of the inputs have requires_grad=True
```

Despite this warning, actual LoRA gradients were nonzero and the optimizer updated trainable parameters.

These warnings are therefore recorded as implementation/environment warnings rather than experiment failures.

---

# 25. Reproducibility

Seed:

```text
42
```

Model:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

Dataset:

```text
Anthropic/hh-rlhf / helpful-base
```

Training examples:

```text
1736
```

Evaluation examples:

```text
200
```

Maximum sequence length:

```text
512
```

DPO beta:

```text
0.1
```

Learning rate:

```text
5e-5
```

LoRA:

```text
r=16
alpha=32
dropout=0.05
q_proj/k_proj/v_proj/o_proj
```

Quantization:

```text
4-bit NF4
double quantization
BF16 compute
```

Generation:

```text
seed=42
temperature=0.7
top_p=0.9
max_new_tokens=128
```

---

# 26. Reproduction Commands

Training:

```bash
python train_scratch_dpo.py \
    --config configs/english_smoke2.yaml
```

Generate initial samples:

```bash
python scripts/generate_dpo_samples.py \
    --step 0
```

Generate checkpoint-25 samples:

```bash
python scripts/generate_dpo_samples.py \
    --checkpoint outputs/dpo_english_m4_2/checkpoint-25 \
    --step 25
```

Generate checkpoint-50 samples:

```bash
python scripts/generate_dpo_samples.py \
    --checkpoint outputs/dpo_english_m4_2/checkpoint-50 \
    --step 50
```

Held-out evaluation:

```bash
python eval/preference_accuracy.py
```

---

# 27. Files Produced

Relevant experiment artifacts:

```text
outputs/dpo_english_m4_2/
├── checkpoint-25/
├── checkpoint-50/
├── preference_accuracy.json
└── samples/
    ├── step-0000.json
    ├── step-0025.json
    └── step-0050.json
```

The experiment is associated with the following implementation components:

```text
train_scratch_dpo.py
scratch_dpo/losses.py
scratch_dpo/forward.py
scratch_dpo/reference.py
scratch_dpo/logps.py
scratch_dpo/collator.py
eval/preference_accuracy.py
scripts/generate_dpo_samples.py
```

---

# 28. Final Assessment

## What passed

The complete scratch DPO pipeline successfully executed on a realistic small English preference dataset.

The following were demonstrated:

1. policy forward pass;
2. reference forward pass;
3. DPO loss computation;
4. gradient computation;
5. LoRA optimization;
6. gradient accumulation;
7. checkpoint saving;
8. checkpoint loading;
9. independent held-out evaluation;
10. fixed-seed generation;
11. absence of obvious catastrophic generation degeneration.


---

## What did not pass

The experiment did **not** demonstrate convincing held-out preference learning.

The strongest checkpoint produced:

```text
Strict preference accuracy: 41.0%
Non-tie accuracy:            47.13%
Tie rate:                    13.0%
Mean margin:                 -0.0538
Mean chosen reward:           0.2729
Mean rejected reward:        0.2763
```

Therefore:

$$
\text{chosen reward} < \text{rejected reward}
$$

on average, and:

$$
\text{preference accuracy}<50\%.
$$

---

# 29. M4.2 Verdict

### **M4.2: EXECUTION PASS / LEARNING VALIDATION NOT DEMONSTRATED**

This is the appropriate conclusion for the experiment.

The result should **not** trigger an immediate rewrite of the DPO implementation.

The underlying mechanics have already passed several stronger correctness checks, including numerical equivalence against TRL's DPO loss.

Instead, the result indicates that this particular:

```text
50-step
batch-size-1
small-LoRA
English smoke run
```

is insufficient to establish successful preference learning.

The experiment therefore successfully validates the **engineering pipeline**, while leaving the **learning behavior** unresolved.
