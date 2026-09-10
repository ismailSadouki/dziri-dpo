# EXP-M4.1 — Manual DPO Training Loop, Checkpointing, and Tiny-Overfit Validation

**Project:** DziriDPO — Algerian Darija Direct Preference Optimization
**Track:** Track A — Pure PyTorch DPO
**Experiment:** M4.1 — Manual DPO training loop with health metrics
**Status:** PASS
**Model:** `Qwen/Qwen2.5-0.5B-Instruct`
**Hardware:** NVIDIA RTX 3050 Laptop GPU, ~3.68 GiB usable VRAM
**Framework:** PyTorch + Transformers + PEFT + bitsandbytes

---

## 1. Objective

The objective of M4.1 was to implement and validate a complete manual DPO training loop in PyTorch.

The experiment was designed to verify that the previously validated DPO components could be connected into an actual optimization pipeline:

$$
(x,y_w,y_l)
\rightarrow
\log\pi_\theta
\rightarrow
\text{DPO loss}
\rightarrow
\nabla_\theta L
\rightarrow
\text{optimizer update}.
$$

The milestone additionally required:

* gradient accumulation;
* gradient clipping;
* health-metric logging;
* LoRA-only optimization;
* checkpoint saving;
* checkpoint reloading;
* optimizer-state restoration;
* resuming training from a checkpoint;
* successful tiny-dataset overfitting.

This experiment was an engineering/correctness validation, not a claim about DPO performance or model quality.

---

## 2. Model and Parameterization

The policy model was:

```text
Qwen/Qwen2.5-0.5B-Instruct
```

The model was loaded using 4-bit NF4 quantization with double quantization.

LoRA was attached to:

```text
q_proj
k_proj
v_proj
o_proj
```

with:

```text
r = 16
alpha = 32
dropout = 0.05
bias = none
```

The resulting parameter counts were:

```text
Total parameters:       496,195,456
Trainable parameters:     2,162,688
Trainable percentage:         0.4359%
```

Only the LoRA parameters were optimized.

---

## 3. Reference-Policy Strategy

The reference policy was implemented using the same base model with the LoRA adapter disabled:

```text
                 Qwen base weights
                  /             \
                 /               \
        LoRA enabled         LoRA disabled
             │                     │
             ▼                     ▼
          policy πθ             reference πref
```

Reference log-probability computation was performed without gradient tracking.

Therefore, the reference policy does not participate in backpropagation.

---

## 4. DPO Objective

For each preference triple

$$
(x,y_w,y_l),
$$

the policy/reference log-ratios are:

$$
r_w =
\log\pi_\theta(y_w|x)
-
\log\pi_{\mathrm{ref}}(y_w|x)
$$

and

$$
r_l =
\log\pi_\theta(y_l|x)
-
\log\pi_{\mathrm{ref}}(y_l|x).
$$

The DPO margin is:

$$
\Delta = r_w-r_l.
$$

With temperature parameter

$$
\beta=0.1,
$$

the per-example loss is:

$$
L =
-\log\sigma(\beta\Delta).
$$

The implementation uses `F.logsigmoid` for numerical stability.

The reward values are:

$$
R_w=\beta r_w
$$

and

$$
R_l=\beta r_l.
$$

Reward accuracy is:

$$
\mathbf{1}[R_w>R_l].
$$

---

## 5. Training Loop

The manual training loop performs the following sequence:

```text
batch
  │
  ├── policy concatenated forward
  │
  ├── reference concatenated forward (no grad)
  │
  ├── DPO loss
  │
  ├── loss scaling for gradient accumulation
  │
  ├── backward()
  │
  ├── gradient accumulation
  │
  ├── gradient clipping
  │
  └── AdamW optimizer step
```

The optimizer is constructed only from parameters with:

```python
parameter.requires_grad == True
```

Gradient clipping uses:

```text
max_grad_norm = 1.0
```

---

## 6. VRAM Constraint and Gradient Accumulation

The available GPU memory is approximately 3.68 GiB.

An initial attempt with:

```yaml
batch_size: 2
gradient_accumulation_steps: 1
```

was able to complete several optimizer steps but subsequently failed with CUDA OOM.

The original log-probability implementation using:

```text
log_softmax → gather
```

was retained because it was mathematically validated and successfully supported the batch-size-1 training configuration.

The final configuration uses:

```yaml
batch_size: 1
gradient_accumulation_steps: 2
```

Therefore:

$$
B_{\mathrm{effective}}
=
B_{\mathrm{micro}}\times G
=
1\times2
=
2.
$$

This preserves an effective batch size of 2 while keeping the instantaneous GPU batch size at 1.

For a 25-optimizer-step run:

```text
50 microsteps
→
25 optimizer steps
```

---

# 7. Experiment A — 25-Step English Smoke Run

## Configuration

```yaml
batch_size: 1
gradient_accumulation_steps: 2
max_steps: 25
learning_rate: 5.0e-5
beta: 0.1
max_grad_norm: 1.0
max_length: 512
```

Dataset:

```text
Anthropic/hh-rlhf
subset: helpful-base
requested examples: 2000
```

During canonicalization/tokenization:

```text
Rejected invalid examples: 77
```

The rejection count was logged and the remaining valid examples were used.

## Result

The run completed all 25 optimizer steps without CUDA OOM.

Representative results:

```text
step 1   loss=0.6931   reward_acc=0.000   margin= 0.0000
step 2   loss=0.6733   reward_acc=1.000   margin= 0.4011
step 3   loss=0.6602   reward_acc=1.000   margin= 0.6709
...
step 21  loss=0.4319   reward_acc=1.000   margin= 6.1578
step 22  loss=0.8500   reward_acc=0.000   margin=-2.9245
step 23  loss=0.7293   reward_acc=0.000   margin=-0.7098
step 24  loss=0.9790   reward_acc=0.000   margin=-5.0790
step 25  loss=0.9027   reward_acc=0.000   margin=-3.8279
```

The individual metrics are highly variable because the microbatch size is 1 and this is only a short smoke run. These values are therefore treated as execution evidence rather than model-performance evidence.

---

# 8. Metric Logging

The training loop writes JSON Lines to:

```text
outputs/dpo_english_smoke/metrics.jsonl
```

Each optimizer step records:

```text
loss
reward_accuracy
margin
chosen_reward
rejected_reward
policy_chosen_logp
policy_rejected_logp
reference_chosen_logp
reference_rejected_logp
chosen_kl_proxy
rejected_kl_proxy
chosen_length
rejected_length
grad_norm
step
learning_rate
gpu_memory_allocated_mb
gpu_memory_reserved_mb
```

The KL fields are explicitly sequence-level policy/reference log-ratio proxies and are not claimed to be exact KL divergence.

Metric logging was successfully verified.

---

# 9. Checkpoint Save

At step 25 the training loop produced:

```text
outputs/dpo_english_smoke/checkpoint-25/
```

The checkpoint contained:

```text
README.md
optimizer.pt
adapter_model.safetensors
config.yaml
adapter_config.json
trainer_state.json
```

The trainer state was:

```json
{
  "global_step": 25,
  "microstep": 50,
  "seed": 42
}
```

This confirms that the checkpoint records both optimizer-step and microstep progress.

---

# 10. Checkpoint Reload Verification

The LoRA adapter was reloaded using:

```python
PeftModel.from_pretrained(
    base_model,
    checkpoint_dir,
    is_trainable=True,
)
```

The reload test verified that:

* the adapter configuration loads;
* trainable LoRA parameters are reconstructed;
* the checkpoint contains trainable adapter parameters;
* independently reconstructed adapter states are numerically identical.

The optimizer checkpoint was then loaded using:

```python
optimizer.load_state_dict(
    optimizer_state
)
```

and the AdamW optimizer state was successfully restored.

Both checkpoint verification tests passed.

---

# 11. Experiment B — Resume From Checkpoint

The training script was extended with:

```text
--resume-from
```

The experiment resumed from:

```text
outputs/dpo_english_smoke/checkpoint-25
```

with:

```text
global_step = 25
microstep   = 50
```

The resumed run correctly began at:

```text
step=0026
```

and continued through:

```text
step=0050
```

without CUDA OOM or training failure.

Representative resumed results:

```text
step 26  loss=0.0791   reward_acc=1.000   margin=25.0000
step 27  loss=0.0864   reward_acc=1.000   margin=24.0000
step 33  loss=0.1270   reward_acc=1.000   margin=20.0000
step 40  loss=0.3008   reward_acc=1.000   margin=10.5000
step 46  loss=0.1396   reward_acc=1.000   margin=19.0000
step 50  loss=0.4844   reward_acc=1.000   margin=4.7500
```

A second checkpoint was successfully produced:

```text
outputs/dpo_english_smoke/checkpoint-50/
```

This validates the complete:

```text
save → reload → restore optimizer → restore counters → resume → save
```

workflow.

---

# 12. Experiment C — Tiny-Overfit Validation

A dedicated tiny preference fixture containing three examples was used:

```text
tiny_001
tiny_002
tiny_003
```

The examples contain deliberately obvious chosen/rejected answers, making them suitable for validating whether the optimization pipeline can memorize a preference signal.

Configuration:

```yaml
batch_size: 1
gradient_accumulation_steps: 1
max_steps: 30
learning_rate: 5.0e-5
beta: 0.1
```

The dataset was repeatedly traversed using the existing training-loop epoch behavior.

## Results

Initial state:

```text
step 1
loss = 0.6931
reward_accuracy = 0.000
margin = 0.0000
```

After only two steps:

```text
step 2
loss = 0.6884
reward_accuracy = 1.000
margin = 0.0948
```

Later:

```text
step 11
loss = 0.1039
reward_accuracy = 1.000
margin = 22.1193
```

```text
step 16
loss = 0.0302
reward_accuracy = 1.000
margin = 34.8366
```

```text
step 21
loss = 0.0095
reward_accuracy = 1.000
margin = 46.5472
```

```text
step 23
loss = 0.0054
reward_accuracy = 1.000
margin = 52.1526
```

```text
step 28
loss = 0.0017
reward_accuracy = 1.000
margin = 63.9140
```

Final step:

```text
step 30
loss = 0.1631
reward_accuracy = 1.000
margin = 17.3087
```

The loss fluctuates because the experiment uses three examples with batch size 1, but the overall learning behavior is clear: the policy rapidly learns the preference ordering.

The run completed without numerical instability or CUDA OOM.

A checkpoint was also saved at:

```text
outputs/dpo_tiny_overfit/checkpoint-30/
```

---

# 13. Validation Summary

| Validation                        | Result |
| --------------------------------- | ------ |
| Manual DPO forward/backward loop  | PASS   |
| Policy/reference separation       | PASS   |
| Reference no-gradient path        | PASS   |
| LoRA-only optimization            | PASS   |
| Gradient accumulation             | PASS   |
| Gradient clipping                 | PASS   |
| Metric logging                    | PASS   |
| 25-step English smoke             | PASS   |
| 50-step resumed training          | PASS   |
| Adapter checkpoint save           | PASS   |
| Adapter checkpoint reload         | PASS   |
| Exact adapter reload verification | PASS   |
| Optimizer state reload            | PASS   |
| Trainer-state restoration         | PASS   |
| Tiny-dataset overfit              | PASS   |
| Tiny-overfit checkpoint           | PASS   |

---

# 14. Known Warnings

The following warnings were observed:

### Gradient checkpointing

PyTorch reports that `use_reentrant` should eventually be specified explicitly.

A second warning reports that checkpoint inputs do not have `requires_grad=True`.

These warnings did not prevent gradient computation: all training experiments produced nonzero gradient norms and successful parameter updates.

They are therefore recorded as technical debt rather than treated as M4.1 blockers.

### Hugging Face Hub authentication

The Hugging Face Hub emitted an unauthenticated-request warning.

This affects download/rate-limit behavior but did not affect the experiment.

---

# 15. Interpretation

M4.1 establishes that the scratch DPO implementation is not merely numerically correct in isolation.

The implementation has now been demonstrated to support the complete optimization lifecycle:

$$
\boxed{
\text{preference batch}
\rightarrow
\text{policy/reference logps}
\rightarrow
\text{DPO loss}
\rightarrow
\text{backpropagation}
\rightarrow
\text{LoRA update}
}
$$

and:

$$
\boxed{
\text{checkpoint}
\rightarrow
\text{reload}
\rightarrow
\text{optimizer restoration}
\rightarrow
\text{training continuation}
}
$$

The tiny-overfit experiment additionally demonstrates that the implementation can learn a deliberately simple preference signal.

These experiments do **not** establish that DPO improves generalization, instruction following, or preference quality. Those questions belong to subsequent evaluation experiments.

---

# 16. Reproducibility Commands

English smoke run:

```bash
rm -rf outputs/dpo_english_smoke

python train_scratch_dpo.py \
    --config configs/english_smoke.yaml
```

Resume run:

```bash
python train_scratch_dpo.py \
    --config configs/english_smoke.yaml \
    --resume-from outputs/dpo_english_smoke/checkpoint-25
```

Tiny-overfit run:

```bash
rm -rf outputs/dpo_tiny_overfit

python train_scratch_dpo.py \
    --config configs/tiny_overfit.yaml
```

Checkpoint reload tests:

```bash
pytest -q tests/test_checkpoint_reload.py -s
```

---

# 17. Final Result

**M4.1 — COMPLETE / PASS**

The manual DPO training loop, health metrics, LoRA-only optimization, checkpointing, checkpoint reload, optimizer restoration, resume functionality, and tiny-overfit validation have all been successfully demonstrated on the constrained RTX 3050 environment.

The project can proceed to:

**M4.2 — Full scratch DPO run + held-out preference evaluation.**
