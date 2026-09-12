# Data Provenance Map

Status values:

- USE: approved for intended use after documented checks
- CANDIDATE: potentially useful; audit required
- HOLD: do not use yet
- EXTERNAL: use only for comparison/evaluation
- CREATE: create ourselves

| Resource | Variety | Type | License reported | Provenance risk | SFT | DPO | Eval | Decision |
|---|---|---|---|---|---|---|---|---|
| Qwen2.5-1.5B-Instruct | Multilingual / Arabic | Model | Apache-2.0 | Model license/revision must be recorded | Base | Base | Base | USE |
| Atlas-Chat | Moroccan Darija | Model | Gemma/model-specific | Different dialect; data mixture heterogeneous | No | No | Comparison | EXTERNAL |
| Atlas Darija-SFT-Mixture | Moroccan Darija | Instruction | ODC-BY; mixed subset licenses | Heterogeneous source licenses | No | No | Related work | EXTERNAL |
| DarijaDZ | Algerian Darija | YouTube corpus | Not clearly specified | Underlying YouTube content / redistribution | HOLD | No | No | HOLD |
| Algerian Darja Corpus | Algerian Darija | Podcast/transcript corpus | CC-BY-4.0 | Underlying source rights require checking | Candidate | No | Possible | CANDIDATE |
| DarjaCore Algerian sample | Algerian Darija | Text corpus | Audit required | Source provenance unclear | Candidate | No | No | CANDIDATE |
| DziriAlign | Algerian Darija | Preference pairs | MIT | Construction/annotation provenance needs audit | No initially | Comparison | Possible | EXTERNAL |
| DziriEval | Algerian Darija | MCQ benchmark | MIT | Evaluation contamination | No | No | Yes | USE |
| ArabicMMLU | MSA | MCQ benchmark | Check source license before redistribution | Not Algerian; evaluation contamination | No | No | Secondary | EXTERNAL |
| DarijaMMLU | Moroccan Darija | Benchmark | Check source license | Different dialect | No | No | Related work | EXTERNAL |
| AlgerianMMLU | Algerian Darija | Planned benchmark | N/A | Not yet established | No | No | Future | FUTURE |

---

## Rules

### Rule 1 — License is necessary but not sufficient

A dataset license on Hugging Face does not automatically prove that every
underlying source item can be redistributed or used without restriction.

For web-derived or platform-derived data, source provenance must also be
considered.

### Rule 2 — Evaluation data stays out of training

Any dataset used as an external evaluation benchmark must not be included
in SFT or DPO training.

### Rule 3 — Moroccan Darija is not Algerian Darija

Moroccan resources can inform methodology and provide cross-dialect
comparisons, but they are not automatically valid Algerian training data.

### Rule 4 — Preference data must have documented construction

Preference datasets should record:

- prompt origin;
- response generation process;
- annotator identity/category where appropriate;
- annotation instructions;
- agreement;
- adjudication;
- rejected-response construction.

### Rule 5 — New project data

The preferred DziriDPO preference-data path is:

our prompts
→ candidate responses
→ human preference annotation
→ double annotation subset
→ agreement analysis
→ final preference dataset.

---

# Planned DziriDPO data layers

## Layer A — Base model

`Qwen/Qwen2.5-1.5B-Instruct`

Role:

Base model only.

---

## Layer B — SFT

Target:

Controlled Algerian-Darija instruction dataset.

Sources:

1. newly created Algerian instruction examples;
2. selected external datasets after provenance audit;
3. permitted transformation of suitable public resources.

Excluded:

- Moroccan-only data;
- evaluation benchmarks;
- sources with unresolved licensing/provenance issues.

---

## Layer C — Preference data

Target:

New human-annotated Algerian-Darija preference dataset.

Minimum planned quality controls:

- explicit annotation guideline;
- at least 100 double-annotated examples;
- inter-annotator agreement;
- disagreement analysis;
- provenance record.

---

## Layer D — Evaluation

Primary:

- DziriEval;
- held-out project evaluation data.

Secondary:

- ArabicMMLU;
- other relevant Arabic evaluation resources.

Future:

- AlgerianMMLU-style benchmark if justified and feasible.

---


TRAINING POLICY

SFT:
- Newly created, documented Algerian-Darija instruction data
- Selected external Algerian resources only after provenance audit
- No evaluation benchmarks
- No Moroccan-Darija data as Algerian training data

DPO:
- Primarily our own human-annotated preference dataset
- External preference datasets are comparison/related-work resources unless independently audited

EVALUATION:
- DziriEval
- Our held-out evaluation set
- ArabicMMLU as a secondary MSA reference
- Never mix evaluation examples into SFT/DPO

HOLD:
- Any dataset whose license or upstream provenance is unclear
- YouTube-derived material when redistribution/training rights cannot be established

* DarjaCore/algerian-darja-sample → CANDIDATE
* touati-kamel/algerian-darja-corpus → CANDIDATE
* nasrellahkharroubi/DarijaDz → HOLD
* touati-kamel/DziriAlign → EXTERNAL / AUDIT
* touati-kamel/DziriEval → USE FOR EVAL ONLY



# Current decision

No external dataset enters the production SFT/DPO pipeline merely because
it is available on Hugging Face.

Every source must first pass:

1. language/variety check;
2. task relevance check;
3. license check;
4. provenance check;
5. contamination check;
6. data-quality check.

Current preferred strategy:

**CREATE + SELECT**, rather than **MERGE EVERYTHING**.