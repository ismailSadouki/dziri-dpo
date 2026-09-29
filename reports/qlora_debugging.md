# QLoRA / LoRA Debugging Log

## B2.2 Smoke Tests

### LoRA BF16

Command:

```bash
python train_sft_trl.py \
    --config configs/sft/lora_bf16.yaml \
    --max-steps 10 \
    --output-dir outputs/sft_lora_bf16_smoke

```

Result: OOM during the first training step.

Configuration:

- Model: Qwen/Qwen2.5-1.5B-Instruct
- Mode: LoRA BF16
- Sequence length: 512
- Batch size: 1
- Gradient accumulation: 8
- Gradient checkpointing: enabled
- LoRA rank: 16
- LoRA alpha: 32
- Target modules: q_proj, k_proj, v_proj, o_proj

Model loading succeeded:

- Total parameters: 1,548,072,448
- Trainable parameters: 4,358,144
- Trainable percentage: 0.2815%

Failure:

- CUDA OOM during TRL chunked cross-entropy computation.
- Additional allocation requested: 892 MiB.
- GPU capacity: 3.68 GiB.
- Free memory at failure: 633.56 MiB.
    
Interpretation:

The 1.5B BF16 base model plus LoRA fits during model loading, but the training forward/loss computation exceeds the available 4-GB GPU memory. This is a measured hardware/configuration limitation, not evidence of an incorrect LoRA setup.



---


### QLoRA NF4

Command:

```bash
python train_sft_trl.py \
    --config configs/sft/qlora_nf4.yaml \
    --max-steps 10 \
    --output-dir outputs/sft_qlora_nf4_smoke
```

Result: PASS.

Model loading:

- Mode: QLoRA NF4
- 4-bit loading: True
- Total parameters reported by the loaded model: 892,974,592
- Trainable parameters: 4,358,144
- Trainable percentage: 0.4880%

Training:

- Steps: 10
- Train loss: 3.800
- Eval loss: 3.622
- Eval mean token accuracy: 0.3659
- No NaN
- No OOM
- Adapter saved successfully

VRAM:

- Peak allocated: 2.39 GB

Interpretation:

QLoRA NF4 completed the full 10-step smoke on the 3.68-GB GPU under the controlled B2.2 configuration. Compared with LoRA BF16, the 4-bit base-model representation made the training workload fit within available GPU memory.



## B2.2 Conclusion

The B2.2 smoke validation is complete.

### Validation gate

- [x] LoRA BF16 model loading works
- [x] QLoRA NF4 model loading works
- [x] QLoRA uses 4-bit loading
- [x] QLoRA calls `prepare_model_for_kbit_training`
- [x] Trainable parameter counts are reported
- [x] Peak VRAM is captured by the TRL callback
- [x] Peak VRAM is independently captured by `measure_peak_vram`
- [x] QLoRA completes a 10-step training smoke
- [x] QLoRA adapter is saved
- [x] No NaN observed
- [x] QLoRA debugging record exists

### Hardware finding

On the RTX 3050 Laptop GPU with approximately 3.68 GiB usable VRAM, the Qwen2.5-1.5B BF16 LoRA configuration loads successfully but cannot complete a training step at the controlled B2.2 configuration.

The QLoRA NF4 configuration completes the same 10-step smoke with approximately 2.39 GB peak allocated VRAM.

Therefore, subsequent SFT experiments on this hardware will use QLoRA NF4 unless a specific experiment requires another loading mode.