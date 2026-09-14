# Preference Dataset Creation Pipeline

This document defines the reusable workflow used to construct preference
datasets for **DziriDPO**.

The goal is to make future preference-dataset construction reproducible,
auditable, and consistent with the methodology used for the first DziriDPO
dataset.

The central principle is:

```text
SFT dataset
→ candidate preference pairs
→ structural validation
→ human preference annotation
→ confound analysis
→ independent annotation
→ agreement analysis
→ final preference dataset
→ DPO training
```

Do not train directly on unreviewed candidate pairs.

---

# Phase 1 — Start from a reviewed SFT dataset

Preference construction starts from an existing, reviewed instruction/SFT
dataset.

Current source:

```text
data/instruction_dataset_v1.jsonl
```

Each source example should contain at least:

```text
id
prompt
response
category
script
```

The original SFT response becomes:

```text
chosen
```

The `chosen` response must not be rewritten during preference construction.

The purpose of preference construction is to create an inferior alternative
to the existing answer and then determine the human preference between the two.

---

# Phase 2 — Freeze the preference guideline

Before generating rejected responses, define the criteria used to judge
response quality.

Current guideline:

```text
data/preference_guideline.md
```

The preference hierarchy is:

1. instruction adherence
2. factual correctness
3. Algerian Darija authenticity
4. fluency / naturalness
5. safety
6. cultural appropriateness
7. helpfulness / completeness
8. conciseness

Important rules:

* Natural code-switching is allowed.
* Script alone must not determine preference.
* Rejected answers must remain plausible.
* Rejected answers must still attempt to answer the prompt.
* Avoid absurd, nonsensical, or obviously broken rejected answers.
* Avoid trivial preference pairs.
* Length must be treated as a potential confound.
* Human preference labels must not simply copy the LLM-generated reason.

The guideline should be frozen before large-scale candidate generation.

---

# Phase 3 — Create a small pilot

Do not immediately generate the complete preference dataset.

First create a small pilot to test the generation protocol and review
workflow.

Current pilot:

```text
data/preference_candidates/pilot_candidates.jsonl
```

Pilot size:

```text
20 pairs
```

The pilot is used to:

* test the rejected-answer generation prompt;
* identify systematic generation problems;
* verify the candidate schema;
* test the validation script;
* test the human-review workflow;
* determine whether the rejected responses are plausible enough for
  large-scale generation.

The pilot should be reviewed before generating the main candidate pool.

---

# Phase 4 — Generate rejected candidates

For every source example:

1. Preserve the original `id`.
2. Preserve the original `prompt`.
3. Preserve the original `category`.
4. Preserve the original `script`.
5. Preserve the original SFT response as `chosen`.
6. Generate exactly one plausible but inferior `rejected`.

The rejected response should contain a meaningful weakness.

Possible failure modes include:

```text
instruction_adherence
factual_correctness
dialect_authenticity
fluency
safety
cultural_appropriateness
helpfulness
conciseness
```

The rejected response should still be a reasonable attempt to answer the
original prompt.

Do not intentionally generate a ridiculous or obviously broken response.

The purpose is to create a realistic preference decision, not an easy
classification problem.

---

# Phase 5 — Candidate JSONL schema

Each candidate pair uses the following top-level fields:

```text
id
prompt
chosen
rejected
source
generation_method
category
script
metadata
```

The `metadata` object should contain:

```text
dialect
preference_reason
rejected_failure_mode
human_review
quality_status
```

Example:

```json
{
  "dialect": "algerian_darija",
  "preference_reason": "factual_correctness",
  "rejected_failure_mode": "factual_correctness",
  "human_review": false,
  "quality_status": "candidate"
}
```

Important:

```text
metadata.preference_reason
```

is a **generation/construction hint**.

It is not the final human preference label.

The LLM may suggest why the rejected response is inferior, but the human
annotator must independently decide which response is preferred.

---

# Phase 6 — Build the main source pool

After the pilot protocol has been tested, construct the source pool for the
main dataset.

Current source pool:

```text
data/preference_candidates/main_source.jsonl
```

Current size:

```text
132 examples
```

Current category balance:

```text
12 examples × 11 categories = 132
```

The source pool contains the reviewed SFT examples that will be converted
into preference candidates.

The original response becomes `chosen`.

The source pool should preserve the original information rather than
rewriting the SFT answers.

---

# Phase 7 — Generate the main candidate dataset

Generate one rejected response for every row in:

```text
data/preference_candidates/main_source.jsonl
```

Output:

```text
data/preference_candidates/main_candidates.jsonl
```

The same generation protocol used during the pilot should be used for the
main dataset.

For reproducibility, record:

* source dataset;
* generation prompt/protocol;
* model used;
* generation method;
* date/version when relevant;
* any generation parameters that materially affect the output.

Do not invent a command for the generation step if generation was performed
through an interactive LLM workflow rather than a reproducible script.

---

# Phase 8 — Validate the candidate JSONL

Before human annotation, validate the generated candidate file.

Use:

```text
scripts/validate_preference_data.py
```

Command:

```bash
python scripts/validate_preference_data.py \
  --input data/preference_candidates/main_candidates.jsonl
```

The validator checks:

* required fields;
* duplicate IDs;
* duplicate preference triples;
* empty fields;
* identical `chosen` / `rejected` responses;
* prompt/response duplication;
* valid script values;
* Algerian Darija metadata;
* valid preference reasons;
* valid rejected failure modes.

Do not proceed while unresolved structural errors remain.

The candidate file is still **unreviewed** at this point.

---

# Phase 9 — Create the human review file

Convert the validated candidate JSONL into the CSV format used for manual
preference annotation.

Use:

```text
scripts/create_preference_review.py
```

For the main dataset:

```bash
python scripts/create_preference_review.py \
  --input data/preference_candidates/main_candidates.jsonl \
  --output data/preference_candidates/main_review.csv
```

For the pilot, the same script can be used:

```bash
python scripts/create_preference_review.py \
  --input data/preference_candidates/pilot_candidates.jsonl \
  --output data/preference_candidates/pilot_review.csv
```

The review file contains:

```text
id
category
script
prompt
chosen
rejected
preference_label
preference_reason
annotator
notes
```

At this stage, the annotation fields are intended for the human reviewer.

The human reviewer determines:

```text
chosen
rejected
tie
```

---

# Phase 10 — Human preference review

For every pair, the human annotator should ask:

> Which response would I actually prefer as the answer to this prompt?

The annotator should evaluate the pair using the preference guideline.

Do not simply accept the LLM-generated `preference_reason`.

The human should record:

```text
preference_label
preference_reason
annotator
notes
```

Possible labels:

```text
chosen
rejected
tie
```

The human label is the authoritative preference decision.

The LLM-generated metadata remains provenance/construction information.

---

# Phase 11 — Check category and label balance

After human review, inspect the resulting review file.

Command:

```bash
python - <<'PY'
import csv
from collections import Counter

path = "data/preference_candidates/main_review.csv"

with open(path, encoding="utf-8", newline="") as f:
    rows = list(csv.DictReader(f))

print("Rows:", len(rows))
print("Preference labels:")
print(Counter(r["preference_label"].strip() for r in rows))

print("\nCategories:")
for category, count in sorted(
    Counter(r["category"].strip() for r in rows).items()
):
    print(f"{category}: {count}")
PY
```

Check:

* total number of reviewed pairs;
* `chosen` / `rejected` / `tie` distribution;
* category distribution;
* missing labels;
* unexpected category imbalance.

For the current DziriDPO dataset, the main review contains:

```text
132 reviewed pairs
132 chosen
0 rejected
0 tie
```

with:

```text
12 pairs per category
11 categories
```

---

# Phase 12 — Analyze length and other preference confounds

A preference dataset can accidentally encode superficial correlations.

For example:

```text
longer response = preferred response
```

rather than:

```text
better response = preferred response
```

Run:

```text
scripts/analyze_preference_confound.py
```

Command:

```bash
python scripts/analyze_preference_confound.py \
  --input data/preference_candidates/main_review.csv
```

Record:

* mean chosen length;
* mean rejected length;
* average length difference;
* longer-response heuristic accuracy.

Interpret the result as a dataset-quality diagnostic, not as proof that
length has no effect.

Other potential confounds should also be considered when relevant, including:

* script;
* category;
* formatting;
* response verbosity;
* repeated lexical patterns;
* systematic characteristics of generated rejected responses.

---

# Phase 13 — Prepare the independent double-annotation sample

Prepare a balanced sample for independent annotation.

Current sample:

```text
data/preference_candidates/kappa_sample_100.csv
```

Current sampling strategy:

```text
9 pairs × 11 categories = 99
+ 1 additional random pair
= 100 pairs
```

Use a fixed random seed so that the sample can be reproduced.

The sample contains separate fields for the two annotators:

```text
annotator_a_label
annotator_a_reason
annotator_a_notes

annotator_b_label
annotator_b_reason
annotator_b_notes
```

Do not copy Annotator A's labels into Annotator B's fields.

The purpose of this sample is to measure independent annotation agreement.

---

# Phase 14 — Independent second annotation

When a second annotator becomes available:

1. Give them the 100-pair sample.
2. Give them the same preference guideline.
3. Do not show them Annotator A's labels.
4. Have them independently label all 100 pairs.
5. Record their reasons and notes independently.
6. Only compare the annotations after both annotators have finished.

Allowed labels:

```text
chosen
rejected
tie
```

The second annotation must be genuinely independent.

Do not manufacture agreement by discussing individual examples before
computing agreement.

---

# Phase 15 — Compute Cohen's κ

After both annotators have completed the 100-pair sample:

Compute Cohen's κ using the two independent label columns.

Then report:

1. Cohen's κ;
2. total agreements;
3. total disagreements;
4. label distribution for each annotator;
5. disagreement categories;
6. systematic disagreement patterns.

Inspect disagreements qualitatively.

If disagreements reveal ambiguity in the guideline, document the issue and
consider updating the guideline for future datasets.

Never invent or estimate Cohen's κ when the second annotation has not
actually been performed.

Current status:

```text
Second annotation: PENDING
Cohen's κ: PENDING
```

---

# Phase 16 — Construct the final preference dataset

Only after human review should the data be considered suitable for DPO
training.

Distinguish clearly between:

```text
main_candidates.jsonl
```

and:

```text
main_review.csv
```

The candidate file contains generated, unverified preference pairs.

The review file contains the human preference decisions.

The final DPO training dataset should be constructed from the **human-reviewed
pairs**, not directly from the candidate JSONL.

Before training:

* remove unresolved ties if the training format requires binary preferences;
* exclude pairs with unresolved quality problems;
* preserve provenance where useful;
* ensure each training pair has a valid preferred and dispreferred response;
* run a final structural validation.

The final training dataset is the dataset actually passed to the DPO pipeline.

---

# Phase 17 — Dataset card / audit report

Create:

```text
reports/preference_label_audit.md
```

The audit report should document:

* source SFT dataset;
* source dataset size;
* preference dataset size;
* category distribution;
* candidate-generation method;
* generation protocol;
* preference guideline;
* human-review procedure;
* human label distribution;
* candidate validation results;
* length/confound analysis;
* independent annotation sample;
* second-annotation status;
* Cohen's κ;
* disagreement analysis;
* known limitations;
* decisions affecting dataset quality.

If an audit step has not been performed, explicitly mark it as:

```text
PENDING
```

Do not report fabricated values.

For example:

```text
Second annotation: PENDING
Cohen's κ: PENDING
```

---

# Complete reusable workflow

For future preference datasets, follow this order:

```text
Reviewed SFT dataset
        ↓
Freeze preference guideline
        ↓
Create small pilot
        ↓
Generate pilot rejected candidates
        ↓
Validate pilot candidates
        ↓
Create pilot review CSV
        ↓
Pilot human review
        ↓
Build main source pool
        ↓
Generate main rejected candidates
        ↓
Validate main candidates
        ↓
Create main review CSV
        ↓
Human preference review
        ↓
Category / label analysis
        ↓
Length / confound analysis
        ↓
Prepare 100-pair double-annotation sample
        ↓
Second independent annotation
        ↓
Cohen's κ
        ↓
Disagreement analysis
        ↓
Construct final preference dataset
        ↓
Dataset card / audit report
        ↓
DPO training
```

---

# Current DziriDPO files

```text
data/
├── instruction_dataset_v1.jsonl
├── preference_guideline.md
└── preference_candidates/
    ├── pilot_candidates.jsonl
    ├── pilot_review.csv
    ├── main_source.jsonl
    ├── main_candidates.jsonl
    ├── main_review.csv
    └── kappa_sample_100.csv

scripts/
├── create_preference_candidates.py
├── create_preference_review.py
├── validate_preference_data.py
├── analyze_preference_confound.py
└── create_kappa_sample.py

reports/
└── preference_label_audit.md

docs/
└── preference_dataset_pipeline.md
```

If `pilot_review.csv` was not retained in the actual repository, remove it
from this tree rather than claiming that it exists.

---

# Important methodological lessons

## 1. Do not jump directly from SFT to DPO

Avoid:

```text
SFT dataset
→ DPO training
```

Use:

```text
SFT
→ candidate rejected responses
→ structural validation
→ human preference review
→ confound analysis
→ independent annotation
→ agreement analysis
→ final preference dataset
→ DPO
```

---

## 2. Candidate generation is not preference annotation

The LLM generates a plausible inferior response.

It does not establish the ground-truth preference label.

The distinction is:

```text
LLM generation
    ↓
candidate pair
    ↓
human preference judgment
    ↓
training preference pair
```

---

## 3. `main_candidates.jsonl` is not the final dataset

It is a candidate pool.

The human-reviewed file is the authoritative source for preference labels.

```text
main_candidates.jsonl
        ↓
human annotation
        ↓
main_review.csv
        ↓
final reviewed preference dataset
        ↓
DPO
```

---

## 4. Human agreement must be measured independently

Do not use the same annotator twice.

Do not copy one annotator's labels into the second annotator's fields.

Do not calculate κ before independent annotation is complete.

If the second annotation has not happened:

```text
Cohen's κ = PENDING
```

---

## 5. Length bias must be measured

A DPO dataset can accidentally teach the model superficial preferences.

Always check whether:

```text
longer → preferred
```

is acting as a shortcut.

The objective is:

```text
quality → preferred
```

rather than:

```text
length → preferred
```

---

## 6. Preserve provenance

For every future preference dataset, preserve enough information to answer:

* Where did the prompt come from?
* What was the original SFT answer?
* How was the rejected answer generated?
* Which model/protocol generated it?
* What failure mode was intended?
* Who performed the human annotation?
* Why was one response preferred?
* Which validation checks were performed?
* Was independent annotation performed?
* What was Cohen's κ?

This makes the dataset useful not only for DPO training, but also for thesis
analysis and future research.

---

# Reproducibility principle

The purpose of this pipeline is not simply to produce preference pairs.

It is to make the entire preference-dataset construction process:

```text
reproducible
auditable
human-validated
measurable
traceable
```

The same workflow can therefore be reused for future Algerian Darija
preference datasets, new domains, or larger versions of DziriDPO without
relying on undocumented steps from the original dataset construction.
