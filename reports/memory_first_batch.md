# M2.1 — First Batch Memory Report

## Model

- Model: Qwen/Qwen2.5-0.5B-Instruct
- Quantization: 4-bit
- Adapter: LoRA
- Reference strategy: adapter_disabled
- PEFT version: 0.17.1


## Precision and Quantization



- Base model quantization: 4-bit
- Quantization type: NF4
- Double quantization: True
- Compute dtype: bfloat16
- LoRA parameter dtype: bfloat16
- Device: CUDA
## Trainable parameters

- Trainable: 2,162,688
- Total: 496,195,456
- Trainable ratio: 0.4359%

## Test input

```text
Hello, how are you?
```

**Shapes**

- input_ids: [1, 5]
- policy logits: [1, 5, 151936]
- reference logits: [1, 5, 151936]

### Reference verification

Maximum absolute difference before training:

0.0

Expected because the LoRA adapter is untrained.

#### VRAM
- Allocated VRAM: 456.62 MB
- Reserved VRAM:  770.00 MB
- Peak VRAM:      460.10 MB


## Decision

Reference strategy:

```
adapter_disabled
```

Reason:

The reference model is obtained by disabling the LoRA adapter on
the same policy model, avoiding loading a second copy of Qwen2.5-0.5B.




