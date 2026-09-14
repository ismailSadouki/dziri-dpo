# SFT Data Creation Pipeline

This document describes the exact workflow used to create, review, validate, and add Algerian Darija instruction data for the DziriDPO SFT dataset.

The same workflow should be repeated for every category (`education`, `daily_life`, `reasoning`, `technical`, etc.).

---

## 1. Pipeline overview

The SFT data pipeline is:

```text
Define category
      ↓
Write generation prompt
      ↓
Generate raw candidates
      ↓
Normalize candidates
      ↓
Create human review sheet
      ↓
Human review
      ↓
accept / edit / reject
      ↓
Build curated SFT JSONL
      ↓
Validate dataset
      ↓
Repeat for next category
```

Important:

* Raw candidates are **not** training data.
* Human-reviewed examples become training data.
* Evaluation datasets must remain separate.
* Do not overwrite the 10-row smoke dataset.
* Each category is processed independently.
* Preserve raw candidates and review files for provenance.

---

# 2. Target schema

## Raw candidate

Raw candidates are stored before human review.

Each candidate should contain:

```json
{
  "candidate_id": "category_name_000001",
  "messages": [
    {
      "role": "user",
      "content": "..."
    },
    {
      "role": "assistant",
      "content": "..."
    }
  ],
  "category": "category_name",
  "script": "arabic",
  "generation_method": "llm",
  "generation_model": "..."
}
```

Raw candidates do NOT receive final `source`, `license`, or `quality_status` until human review.

---

# 3. Step 1 — Choose the category

Choose one category and generate a small batch first.

Current categories:

```text
education
general_qa
reasoning
daily_life
algerian_culture
commerce
translation
code_switching
technical
safety
humor
```

Recommended first-round target:

```text
20 candidates per category
```

This gives:

```text
11 categories × 20 = 220 examples
```

before scaling to the larger dataset.

---

# 4. Step 2 — Create the category prompt

Create a directory for the category:

```bash
mkdir -p data/sft_candidates/<CATEGORY>
```

Example:

```bash
mkdir -p data/sft_candidates/daily_life
```

Create the generation prompt:

```bash
nano data/sft_candidates/daily_life/prompt.txt
```

The prompt should require:

* natural Algerian Darija
* Arabic script preferred
* natural French/English technical terms when appropriate
* no Moroccan Darija
* avoid unnecessary MSA
* realistic user questions
* useful assistant answers
* factual correctness
* diversity
* no benchmark copying
* no references to AI generation
* JSONL output
* exactly the required candidate schema

For example, the next category after education is:

```text
daily_life
```

Generate approximately 20 candidates.

---

# 5. Step 3 — Store raw generated data

Save the generated JSONL without modifying the candidate content.

Example:

```text
data/sft_candidates/daily_life/raw.jsonl
```

Do not manually convert it into the final SFT dataset yet.

The raw generation should remain available for provenance.

---

# 6. Step 4 — Normalize candidates

Use:

```bash
python scripts/generate_sft_candidates.py \
    --input data/sft_condidates/<CATEGORY>/raw.jsonl \
    --output data/sft_condidates/<CATEGORY>/candidates.jsonl
```

The normalizer checks things such as:

* valid JSON
* required fields
* exactly two messages
* correct user/assistant roles
* non-empty content
* unique candidate IDs

The normalized candidates should be stored as:

```text
data/sft_candidates/<CATEGORY>/candidates.jsonl
```

If the current normalization script is category-specific, preserve the category-specific raw file and use the same normalization logic for the next category.

Expected result:

```text
CANDIDATE NORMALIZATION: PASS
Candidates: 20
Unique IDs: 20
Output: data/sft_candidates/candidates.jsonl
```

---

# 7. Step 5 — Create the review sheet

Create the human-review CSV:

```bash
python scripts/create_sft_review.py \
    --input data/sft_condidates/<CATEGORY>/candidates.jsonl \
    --output data/sft_review/<CATEGORY>_review.csv
```

This produces:

```text
data/sft_review/<CATEGORY>_review.csv
```

The review sheet contains:

```text
candidate_id
category
script
user_text
assistant_text
decision
dialect_ok
factual_ok
instruction_ok
natural_ok
edited_user_text
edited_assistant_text
notes
```

---

# 8. Step 6 — Human review

Review every candidate.

For each row, fill:

### `decision`

Allowed values:

```text
accept
edit
reject
```

### `dialect_ok`

```text
yes
no
```

Check whether the language is genuinely Algerian Darija.

### `factual_ok`

```text
yes
no
```

Check whether the answer is factually correct.

### `instruction_ok`

```text
yes
no
```

Check whether the assistant actually answered the user's request.

### `natural_ok`

```text
yes
no
```

Check whether the response sounds natural rather than translated or artificial.

### `edited_user_text`

Leave empty for `accept`.

If the user prompt needs correction:

```text
edit
```

and put the corrected prompt here.

### `edited_assistant_text`

Leave empty for `accept`.

If the assistant response needs correction:

```text
edit
```

and put the corrected answer here.

### `notes`

Briefly explain the decision when useful.

Examples:

```text
Clear and natural
```

```text
Good Darija, appropriate code-switching
```

```text
Correct answer but slightly unnatural phrasing
```

```text
Too MSA-heavy
```

```text
Factual error
```

---

# 9. Annotation hierarchy

When deciding whether an answer is good, use this priority order:

```text
1. Instruction adherence
2. Factual correctness
3. Algerian Darija authenticity
4. Fluency and clarity
5. Safety / appropriateness
6. Concise helpfulness
```

Length is NOT automatically better.

A shorter answer that correctly solves the problem is preferable to unnecessary verbosity.

---

# 10. Code-switching policy

Do not automatically reject French or English.

Natural Algerian Darija commonly contains technical or contextual code-switching.

Examples of acceptable terminology include:

```text
moyenne
variance
écart-type
overfitting
fine-tuning
dataset
Python
```

The question is:

> Is the code-switching natural and useful?

Not:

> Is every word Arabic?

---

# 11. Script policy

Allowed scripts:

```text
arabic
arabizi
mixed
```

Do not automatically prefer Arabic script over Arabizi.

Judge:

* readability
* naturalness
* consistency
* appropriateness to the context

---

# 12. Step 7 — Inspect review statistics

After reviewing a batch, run:

```bash
python - <<'PY'
import csv
from collections import Counter

path = "data/sft_review/review.csv"

with open(path, encoding="utf-8") as f:
    rows = list(csv.DictReader(f))

print("Candidates:", len(rows))
print("Decisions:", Counter(r["decision"] for r in rows))
print("Dialect:", Counter(r["dialect_ok"] for r in rows))
print("Factual:", Counter(r["factual_ok"] for r in rows))
print("Instruction:", Counter(r["instruction_ok"] for r in rows))
print("Natural:", Counter(r["natural_ok"] for r in rows))
PY
```

Example:

```text
Candidates: 20
Decisions: Counter({'accept': 18, 'edit': 2})
Dialect: Counter({'yes': 20})
Factual: Counter({'yes': 19, 'no': 1})
Instruction: Counter({'yes': 20})
Natural: Counter({'yes': 18, 'no': 2})
```

Do not expect every category to have 20/20 acceptance.

The purpose of review is to remove bad examples.

---

# 13. Step 8 — Build curated SFT dataset

Use:

```bash
python scripts/build_sft_dataset.py \
    --input data/sft_review/<CATEGORY>_review.csv
```

The converter applies:

```text
accept
    ↓
keep original user + assistant

edit
    ↓
use edited text

reject
    ↓
discard
```

The output is:

```text
data/instruction_dataset_v1.jsonl
```

The converter adds provenance metadata:

```json
{
  "source": "synthetic_then_human_verified",
  "license": "project-created",
  "metadata": {
    "dialect": "algerian_darija",
    "code_switching": "allowed",
    "quality_status": "accepted",
    "generation_method": "llm",
    "human_review": true,
    "review_decision": "accept",
    "review_notes": "..."
  }
}
```

---

# 14. Step 9 — Validate the curated dataset

Run:

```bash
python scripts/validate_sft_data.py \
    --input data/instruction_dataset_v1.jsonl
```

The validator checks:

* valid JSON
* required fields
* unique IDs
* exactly two messages
* correct roles
* non-empty content
* valid categories
* valid scripts
* provenance fields
* Algerian Darija metadata
* duplicate user/assistant pairs
* maximum content length

Expected:

```text
SFT DATA VALIDATION: PASS
Rows: 20
Unique IDs: 20
Unique pairs: 20
Categories: {'education': 20}
Scripts: {'arabic': 20}
```

---

# 15. Step 10 — Repeat for the next category

Do NOT manually invent a new workflow.

Repeat:

```text
1. Choose category
2. Create category prompt
3. Generate ~20 candidates
4. Save raw JSONL
5. Normalize
6. Create review sheet
7. Human review
8. Inspect review statistics
9. Build curated SFT JSONL
10. Validate
```


---

# 16. Current status

First batch:

```text
Category: education
Candidates: 20
Accepted: 20
Edited: 0
Rejected: 0
Dialect OK: 20
Factual OK: 20
Instruction OK: 20
Natural OK: 20
Validation: PASS
```

Current curated file:

```text
data/instruction_dataset_v1.jsonl
```

The original smoke dataset remains:

```text
data/instruction_dataset.jsonl
```

Do not overwrite the smoke dataset.

---

# 17. Important data philosophy

The goal is NOT:

```text
generate 800 examples → train
```

The goal is:

```text
generate
   ↓
filter
   ↓
human verify
   ↓
edit/reject
   ↓
validate
   ↓
train
```

The LLM is being used to accelerate candidate generation.

The human review is what makes the final dataset curated.

Therefore:

> Raw synthetic data is not automatically high-quality SFT data.

---

# 18. Scaling strategy

Start with:

```text
20/category
```

Then inspect the quality.

If the quality remains high, scale toward approximately:

```text
600–1000 total SFT examples
```

while maintaining category diversity.

Do not blindly maximize the number of examples.

Quality, diversity, provenance, and consistency matter more than raw size.

---

# 19. Quick checklist

When starting a new category, use this checklist:

```text
[ ] mkdir -p data/sft_candidates/<category>

[ ] create generation prompt

[ ] generate ~20 raw candidates

[ ] normalize candidates

[ ] run candidate normalizer

[ ] create review.csv

[ ] review every candidate

[ ] accept / edit / reject

[ ] fill dialect/factual/instruction/natural flags

[ ] add notes where useful

[ ] run review statistics

[ ] build curated SFT dataset

[ ] validate curated JSONL

[ ] record category count

[ ] move to next category
```

### One-line memory aid

```text
GENERATE → NORMALIZE → REVIEW → BUILD → VALIDATE → NEXT CATEGORY
```

That is the workflow to reuse every time.
