## Track B — DPO B3.1

### 1. Train each β configuration

```bash
python train_dpo_trl.py --config configs/dpo/beta_0.05.yaml
python train_dpo_trl.py --config configs/dpo/beta_0.1.yaml
python train_dpo_trl.py --config configs/dpo/beta_0.3.yaml
python train_dpo_trl.py --config configs/dpo/beta_0.5.yaml
```

If your script is under another path, use that path before `train_dpo_trl.py`.

### 2. Verify the outputs

```bash
find outputs/dpo_beta_0.05 -maxdepth 2 -type f | sort
find outputs/dpo_beta_0.1 -maxdepth 2 -type f | sort
find outputs/dpo_beta_0.3 -maxdepth 2 -type f | sort
find outputs/dpo_beta_0.5 -maxdepth 2 -type f | sort
```

Expected important artifacts:

```text
run_summary.json
checkpoint-50/
adapter_model.safetensors
adapter_config.json
training_args.bin
trainer_state.json
```

### 3. Inspect the evaluation metrics

```bash
python darija_alignment/plot_dpo_metrics.py
```

This also became the main Track-B B3.2 metric/plot extraction script.

---

# Track B — DPO B3.2

### 1. Extract the β metrics

You already used:

```bash
python darija_alignment/extract_dpo_metrics.py
```

This produces:

```text
reports/darija_alignment/beta_0.05.json
reports/darija_alignment/beta_0.1.json
reports/darija_alignment/beta_0.3.json
reports/darija_alignment/beta_0.5.json
reports/darija_alignment/beta_metrics.json
```

### 2. Generate the β plots

```bash
python darija_alignment/plot_dpo_metrics.py
```

Produces:

```text
reports/darija_alignment/plots/
├── beta_vs_reward_accuracy.png
├── beta_vs_kl_proxy.png
├── beta_vs_response_length.png
├── beta_vs_eval_margin.png
├── beta_vs_logps_chosen.png
├── beta_vs_eval_loss.png
├── beta_sweep_final_summary.png
├── training_margin_by_beta.png
├── training_chosen_reward_by_beta.png
├── training_logps_chosen_by_beta.png
├── training_kl_proxy_by_beta.png
└── training_health_summary.png
```

and:

```text
reports/darija_alignment/b3_2_plot_summary.json
```

### 3. Verify generation evaluation

Your generation evaluation covers:

```text
SFT
β=0.05
β=0.10
β=0.30
β=0.50
```

with:

```text
44 fixed prompts
greedy decoding
max_new_tokens=256
seed=42
```

Then inspect:

```bash
cat reports/darija_alignment/generations/generation_summary.json
```

### 4. Check all B3.2 artifacts

```bash
find reports/darija_alignment -maxdepth 3 -type f | sort
```

### 5. Git status

```bash
git status --short
```

### 6. Review the complete Track-B diff

```bash
git diff --stat
```

and:

```bash
git diff
```

### 7. Commit B3.1 + B3.2

After verifying everything:

```bash
git add configs/dpo \
        darija_alignment \
        reports/darija_alignment
```

Then:

```bash
git status
```

Commit:

```bash
git commit -m "Complete Track B DPO B3.1 and B3.2 beta sweep"
```

Then:

```bash
git push
```

### Minimal rerun sequence

If you just want the **commands you need from the current state onward**, it's:

```bash
python darija_alignment/extract_dpo_metrics.py
python darija_alignment/plot_dpo_metrics.py
find reports/darija_alignment -maxdepth 3 -type f | sort
git status --short
```

**B3.1 = DPO training/configuration.  
B3.2 = β sweep + health metrics + generation diagnostics + candidate β selection.**
