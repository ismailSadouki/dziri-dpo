
# DziriDPO Preference Dataset — Label Audit Report

## 1. Overview

This report documents the construction and quality-control process for the
Algerian Darija preference dataset used in DziriDPO.

The preference dataset is built from a reviewed Algerian Darija instruction
dataset. The original SFT response is retained as `chosen`, while one plausible
but inferior response is generated as `rejected`.

The LLM is used to generate candidate rejected responses, but the final
preference decision is made by human review.

---

## 2. Source Dataset

Source:

`data/instruction_dataset_v1.jsonl`

Dataset size:

- 220 reviewed instruction examples
- 20 examples per category
- 11 categories

Categories:

- education
- daily_life
- general_qa
- reasoning
- algerian_culture
- commerce
- translation
- code_switching
- technical
- safety
- humor

---

## 3. Preference Construction

### Pilot

Pilot file:

`data/preference_candidates/pilot_candidates.jsonl`

Size:

- 20 preference candidates

The pilot was manually reviewed before constructing the main preference pool.

### Main candidate pool

Source pool:

`data/preference_candidates/main_source.jsonl`

Size:

- 132 source examples
- 12 examples per category

Generated candidates:

`data/preference_candidates/main_candidates.jsonl`

Human review:

`data/preference_candidates/main_review.csv`

---

## 4. Preference Pair Schema

Candidate JSONL fields:

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

The original SFT response is preserved as `chosen`.

Exactly one plausible but inferior response is generated as `rejected`.

The rejected response must remain a reasonable attempt to answer the prompt.
It should contain a meaningful weakness rather than being absurd, empty,
unrelated, or obviously broken.

---

## 5. Preference Guideline

The preference hierarchy is:

1. Instruction adherence
2. Factual correctness
3. Algerian Darija authenticity
4. Fluency / naturalness
5. Safety
6. Cultural appropriateness
7. Helpfulness / completeness
8. Conciseness

Natural code-switching is allowed.

Script choice alone must not determine preference.

The preference guideline is documented in:

`data/preference_guideline.md`

---

## 6. Human Review

Human review file:

`data/preference_candidates/main_review.csv`

Reviewed pairs:

**132 / 132**

Preference labels:

* chosen: 132
* rejected: 0
* tie: 0

Category distribution:

| Category         | Reviewed |
| ---------------- | -------: |
| algerian_culture |       12 |
| code_switching   |       12 |
| commerce         |       12 |
| daily_life       |       12 |
| education        |       12 |
| general_qa       |       12 |
| humor            |       12 |
| reasoning        |       12 |
| safety           |       12 |
| technical        |       12 |
| translation      |       12 |
| **Total**        |  **132** |

The model-generated preference reason is treated as metadata only.
Human review determines the actual preference label.

---

## 7. Automated Validation

Validator:

`scripts/validate_preference_data.py`

The validator checks:

* required fields
* duplicate IDs
* duplicate preference triples
* empty prompts/responses
* identical chosen/rejected responses
* prompt/response duplication
* valid script values
* Algerian Darija metadata
* valid preference reasons
* rejected failure-mode metadata

The candidate datasets were validated before proceeding.

---

## 8. Length / Confound Analysis

Analysis script:

`scripts/analyze_preference_confound.py`

The analysis compares chosen and rejected response lengths and measures the
accuracy of a simple longer-response heuristic.

This is important because preference datasets can accidentally encode:

> longer response = better response

rather than the intended qualitative preference.

The length analysis should therefore be reported alongside DPO results.

A numeric result should only be reported when reproduced from the saved script
output.

---

## 9. Double-Annotation Sample

Prepared sample:

`data/preference_candidates/kappa_sample_100.csv`

Sample size:

**100 pairs**

Sampling strategy:

* 9 pairs from each of the 11 categories = 99
* 1 additional randomly selected reviewed pair = 100
* random seed: 42

The sample contains independent fields for:

* Annotator A label/reason/notes
* Annotator B label/reason/notes

Annotator B fields remain empty until an independent second annotator is
available.

---

## 10. Cohen's Kappa Status

Cohen's κ has **not yet been computed**.

Reason:

A second independent annotator is not currently available.

Current status:

| Component             | Status   |
| --------------------- | -------- |
| Annotator A           | Complete |
| Annotator B           | Pending  |
| Cohen's κ             | Pending  |
| Disagreement analysis | Pending  |

No κ value is fabricated or estimated.

When a second annotator becomes available, both annotators must independently
label the same 100 pairs before calculating κ.

---

## 11. Manual Audit Status

A separate 50-pair manual audit was not performed.

Reason:

The complete 132-pair main candidate set was already manually reviewed.

This is recorded explicitly rather than presenting the 50-pair audit as
completed.

---

## 12. Current Status

Completed:

* [x] Preference schema defined
* [x] Preference guideline written
* [x] 20-pair pilot generated
* [x] Pilot manually reviewed
* [x] Candidate validator implemented
* [x] 132-row main source pool created
* [x] 132 candidate pairs generated
* [x] 132 candidate pairs manually reviewed
* [x] Length/confound analysis performed
* [x] 100-pair double-annotation sample prepared

Pending:

* [ ] Independent second annotation
* [ ] Cohen's κ
* [ ] Disagreement analysis

---

## 13. Limitations

The current preference dataset has several limitations:

1. Rejected responses were generated by an LLM and therefore may contain
   generation artifacts.
2. Only one human annotator has currently performed the preference review.
3. Cohen's κ cannot be computed until an independent second annotation exists.
4. The dataset is relatively small and should not be treated as a definitive
   benchmark of Algerian Darija preferences.
5. Length bias must be considered when interpreting DPO results.

These limitations should be addressed in future dataset iterations.

---

## 14. Reproducibility

The complete construction workflow is documented in:

`docs/preference_dataset_pipeline.md`

The workflow should be reused for future preference datasets rather than
creating preference pairs ad hoc.

