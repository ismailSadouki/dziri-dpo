# Reference Policy — scratch DPO

## Strategy

`Scratch DPO` uses the adapter-disabled reference strategy.

The policy and reference share the same base model.

During reference evaluation, the LoRA adapter is disabled:

```python
with model.disable_adapter():
    ...
```

The reference forward pass is performed under:

```python
with torch.no_grad():
    ...
```
Reference log-probabilities are detached before being returned.

**Why**

Loading a second copy of the Qwen model would unnecessarily increase
GPU memory usage.

With LoRA, the reference policy can be represented by the frozen base
model with the policy adapter disabled.

Therefore:

$$
\Pi_{ref} = \Pi_{base}
$$

and:

$$
\Pi_\theta = \Pi_{base} + LoRa_\theta
$$

during policy evaluation.


**Precomputed reference log-probabilities**

Not used for the initial Track A implementation.

Online reference computation is preferred because it avoids cache
invalidation complexity.

If precomputation is introduced later, the cache must be invalidated
when any of the following changes:

- model version
- tokenizer version
- chat-template version
- preference dataset version
- data preprocessing version
- sequence formatting
- truncation configuration

