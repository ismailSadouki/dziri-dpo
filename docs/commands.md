# Project Commands

This file records important commands used throughout the project.
The goal is to make the project reproducible without relying on memory
or previous conversations.

---

## Environment

### Activate environment

```bash
conda activate ml-dl
```

### Run tests

```bash
pytest -q
```
Use this after modifying source code to verify that existing
correctness tests still pass.

### M1.2 — Build HH-RLHF canonical dataset

```bash
python scratch_dpo/dataset.py
```

**Purpose**

Downloads/loads the HH-RLHF dataset, selects a deterministic
2,000-example slice using the project seed, converts the raw
HH-RLHF conversations into the canonical preference schema, and
writes the resulting JSONL dataset.


**Input**

```txt
Anthropic/hh-rlhf
subset: helpful-base
split: train
seed: 42
```

**Output**

```txt
data/english/hh_rlhf_helpful-base_2000.jsonl
```

The loader may also write rejected examples to:
```txt
data/english/hh_rlhf_rejected.jsonl
```




### M1.3 — Response-mask audit

```bash
python scripts/audit_response_mask.py
```

**Purpose**

Generate a human-readable audit showing which tokens belong
to the prompt and which belong to the assistant response.

**Expected structure:**

```
P P P P P P R R R R
```

Prompt tokens must have:

```
loss_mask = 0
```


Response tokens must have:

```
loss_mask = 1
```

**Output**

```
reports/response_mask_audit.md
```


### M1.4 — Collator audit

```bash
python scripts/audit_collator.py
```

**Purpose**

Verify that the DPO collator correctly creates:

- input IDs
- attention masks
- response loss masks
- padding

and that padding positions never contribute to the loss.

Expected conceptual structure:


```
P P P R R R PAD PAD
P P P P R R R R PAD
```

with:

attention_mask:
```
1 1 1 1 1 1 0 0
```

loss_mask:
```
0 0 0 1 1 1 0 0
```

### M1.4 — Validate preference dataset

```bash
python scratch_dpo/validate_preference_data.py \
    data/english/hh_rlhf_helpful-base_2000.jsonl
```

**Purpose**

Run the pre-flight validation of the canonical preference dataset.

Checks include:

- empty prompts
- empty chosen responses
- empty rejected responses
- identical chosen/rejected responses
- duplicate IDs
- basic preference-data validity
- response length statistics


**Input**

```txt
data/english/hh_rlhf_helpful-base_2000.jsonl
```

**Output**

```txt
reports/preference_data_audit.md
```

---

# M2 — Log probabilities

## M2.1 — Model loading audit

```bash
python scripts/test_policy_forward.py
```

