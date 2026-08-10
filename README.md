# DziriDPO

**End-to-end DPO alignment pipeline from scratch.** Implements DPO mechanics in pure PyTorch with numerical verification against TRL, followed by SFT and DPO training, preference data construction, annotation agreement, and evaluation for Algerian Darija alignment.

> **Public framing:** verified DPO mechanics + Darija alignment methodology — not simply “I fine-tuned a model.”

---

## Overview

DziriDPO is a two-stage project for understanding and building Direct Preference Optimization (DPO) systems.

The project deliberately separates **mechanical verification** from **production alignment**:

```text
                    DziriDPO
                       │
          ┌────────────┴────────────┐
          │                         │
          ▼                         ▼
   Scratch DPO                Darija Alignment
   Pure PyTorch                    TRL
          │                         │
          ▼                         ▼
   DPO mechanics             Data + SFT + DPO
          │                         │
          ▼                         ▼
   TRL numerical oracle      Triple-axis evaluation
          │                         │
          └────────────┬────────────┘
                       ▼
             Reproducible results
```

The central correctness claim is:

[
\left|
\mathcal{L}_{\text{scratch}}
----------------------------

\mathcal{L}_{\text{TRL}}
\right|
<10^{-5}
]

on identical inputs, models, masks, reference log-probabilities, and DPO hyperparameters.

Only after this verification does the project move to the production Darija alignment pipeline.

---

## Project Goals

### 1. Understand DPO mechanically

Implement the core DPO computation without relying on a high-level DPO trainer:

* preference triples
* chat templating
* response-only masks
* shifted token probabilities
* gathered token log-probabilities
* sequence-level log-probabilities
* chosen/rejected policy scores
* reference-model scores
* DPO logits
* DPO loss
* training loop
* health metrics

### 2. Verify the implementation

Compare the pure-PyTorch implementation against TRL using the same inputs.

The main correctness oracle is:

```python
torch.allclose(
    scratch_loss,
    trl_loss,
    atol=1e-5,
)
```

The comparison is performed progressively:

```text
token log-probs
      ↓
chosen/rejected log-probs
      ↓
reference log-probs
      ↓
policy/reference log-ratios
      ↓
DPO margin
      ↓
final DPO loss
```

### 3. Build a reproducible Algerian Darija alignment pipeline

The production pipeline covers:

```text
Darija resource survey
        ↓
preference guideline
        ↓
SFT instruction data
        ↓
preference pairs
        ↓
annotation agreement
        ↓
SFT
        ↓
LoRA / QLoRA sweep
        ↓
DPO
        ↓
evaluation
```

### 4. Evaluate alignment beyond training loss

The final evaluation uses three complementary axes:

| Axis       | Evaluation                   |
| ---------- | ---------------------------- |
| Knowledge  | AlgerianMMLU                 |
| Preference | Held-out preference accuracy |
| Generation | Generation win rate          |

Qualitative analysis is also performed on **30+ DPO generations**.

---

# Project Structure

```text
dziri-dpo/
├── configs/
│   ├── scratch_dpo.yaml
│   ├── english_smoke.yaml
│   ├── sft_baseline.yaml
│   ├── sft_sweep.yaml
│   └── dpo_sweep.yaml
│
├── scratch_dpo/
│   ├── dataset.py
│   ├── collator.py
│   ├── logprobs.py
│   ├── reference.py
│   ├── loss.py
│   └── train.py
│
├── darija_alignment/
│   ├── data/
│   │   ├── survey.md
│   │   ├── guideline.md
│   │   ├── build_sft.py
│   │   └── build_preferences.py
│   │
│   ├── annotation/
│   │   └── agreement.py
│   │
│   ├── sft.py
│   ├── dpo.py
│   └── evaluate.py
│
├── eval/
│   ├── preference_accuracy.py
│   ├── win_rate.py
│   ├── algerian_mmlu.py
│   ├── judge.py
│   └── qualitative.py
│
├── tests/
│   ├── test_masks.py
│   ├── test_logprobs.py
│   ├── test_reference.py
│   ├── test_dpo_loss.py
│   ├── test_trl_parity.py
│   └── test_overfit_tiny.py
│
├── scripts/
│   ├── prepare_english.py
│   ├── run_scratch_dpo.py
│   ├── run_sft.py
│   ├── run_dpo.py
│   └── evaluate.py
│
├── reports/
│   ├── scratch_parity.md
│   ├── dpo_health.md
│   ├── annotation_agreement.md
│   ├── sft_sweep.md
│   ├── dpo_sweep.md
│   ├── evaluation.md
│   └── failure_taxonomy.md
│
├── notes/
│   ├── decisions.md
│   ├── dpo-derivation.md
│   ├── data-guideline.md
│   ├── runs.md
│   └── bugs/
│
├── README.md
├── pyproject.toml
└── LICENSE
```

---

# DPO Background

DPO starts from preference triples:

[
(x,y_w,y_l)
]

where:

* (x) = prompt
* (y_w) = preferred/chosen response
* (y_l) = rejected response

Given a policy (\pi_\theta) and reference policy (\pi_{\mathrm{ref}}), the DPO objective is:

[
\mathcal{L}_{\mathrm{DPO}}
==========================

-\log
\sigma
\left(
\beta
\left[
\log
\frac{\pi_\theta(y_w|x)}
{\pi_{\mathrm{ref}}(y_w|x)}
---------------------------

\log
\frac{\pi_\theta(y_l|x)}
{\pi_{\mathrm{ref}}(y_l|x)}
\right]
\right)
]

Equivalently:

[
\mathcal{L}_{\mathrm{DPO}}
==========================

-\log
\sigma
\left(
\beta
\left[
r_w-r_l
\right]
\right)
]

where

[
r_w =
\log\pi_\theta(y_w|x)
---------------------

\log\pi_{\mathrm{ref}}(y_w|x)
]

and

[
r_l =
\log\pi_\theta(y_l|x)
---------------------

\log\pi_{\mathrm{ref}}(y_l|x).
]

The scratch implementation explicitly computes each of these quantities instead of hiding them behind a trainer abstraction.

---

# Scratch DPO

## Data

Each example is represented as:

```text
(prompt, chosen, rejected)
```

The tokenization pipeline constructs:

```text
prompt + chosen
prompt + rejected
```

and creates response-only masks so that prompt tokens do not contribute to the sequence log-probability.

For a sequence of tokens

[
y=(y_1,\ldots,y_T)
]

the response log-probability is:

[
\log \pi(y|x)
=============

\sum_{t=1}^{T}
m_t
\log
\pi(y_t|x,y_{<t})
]

where

[
m_t\in{0,1}
]

is the response mask.

---

## Log-probability computation

The implementation explicitly performs:

```text
logits
  ↓
shift
  ↓
log_softmax
  ↓
gather target token
  ↓
apply response mask
  ↓
sum
```

The result is one scalar sequence log-probability per example.

For a batch size (B):

[
\mathbf{L}\in\mathbb{R}^{B}
]

rather than token-level losses.

---

# Numerical Verification

The most important test in the repository is the TRL parity test.

Given identical:

* model parameters
* reference parameters
* input IDs
* attention masks
* response masks
* chosen/rejected sequences
* (\beta)

the scratch implementation and TRL should produce numerically equivalent DPO losses.

```python
assert torch.allclose(
    scratch_loss,
    trl_loss,
    atol=1e-5,
)
```

The target is:

[
|\mathcal{L}*{scratch}-\mathcal{L}*{TRL}|<10^{-5}.
]

This is the project's primary **correctness oracle**.

---

# Scratch Training

After numerical verification, the scratch implementation is used for a small English preference-training run.

The run is intentionally limited in scope. Its purpose is not to produce a competitive English model, but to verify that the implementation behaves correctly during optimization.

Tracked health metrics include:

* training loss
* preference/reward accuracy
* chosen log-probability
* rejected log-probability
* policy/reference KL-related statistics
* reward margin
* response length
* length drift
* held-out preference accuracy

The project also deliberately records potential degeneration behavior.

---

# Darija Alignment

The second stage moves from mechanics to a production-oriented Algerian Darija pipeline.

## Data methodology

The data pipeline starts with a resource and provenance survey:

```text
existing resources
      ↓
provenance
      ↓
selection criteria
      ↓
SFT dataset
      ↓
preference dataset
```

Every preference pair follows the canonical format:

```text
prompt
chosen
rejected
```

---

# Preference Annotation

Before large-scale preference collection, a Darija-specific annotation guideline is defined.

The guideline answers:

> **What makes one response better than another in Algerian Darija?**

The annotation criteria are designed to capture properties such as:

* instruction following
* factual correctness
* relevance
* clarity
* natural Darija usage
* appropriate code-switching
* cultural/contextual appropriateness
* harmful or misleading content

The exact criteria and examples are documented in:

```text
darija_alignment/data/guideline.md
```

---

# Inter-Annotator Agreement

A subset of at least **100 preference pairs** is independently double-annotated.

Cohen's kappa is computed as:

[
\kappa
======

\frac{p_o-p_e}{1-p_e}
]

where:

* (p_o) = observed agreement
* (p_e) = expected agreement by chance

The project reports:

* number of double-annotated pairs
* observed agreement
* expected agreement
* Cohen's (\kappa)
* disagreement categories
* examples of disagreements
* guideline revisions resulting from disagreements

This provides evidence that the preference labels are not simply arbitrary choices.

---

# SFT

Before DPO, the selected base model is adapted to the Darija instruction dataset using supervised fine-tuning.

The SFT experiments investigate:

### Target modules

```text
q, v
q, k, v, o
all linear
```

### Rank

The sweep includes different LoRA ranks, beginning with:

[
r=16
]

as the fixed-rank baseline for target-module comparisons.

### LoRA vs QLoRA

Both adaptation strategies are compared where hardware permits.

### Data fraction

Different fractions of the available SFT data are evaluated.

---

# SFT Experiment Table

The final SFT report records at least:

| Configuration  | Quality | VRAM | Speed |
| -------------- | ------: | ---: | ----: |
| LoRA           |       — |    — |     — |
| QLoRA          |       — |    — |     — |
| target modules |       — |    — |     — |
| rank           |       — |    — |     — |
| data fraction  |       — |    — |     — |

The objective is not simply to find the highest score.

The selected configuration should represent a reasonable trade-off between:

[
\text{quality}
\quad
\text{VRAM}
\quad
\text{training speed}.
]

---

# DPO Training

The best SFT checkpoint becomes the starting point for production DPO.

The production pipeline uses TRL.

The DPO sweep investigates the effect of:

[
\beta
]

while tracking:

* reward/preference accuracy
* chosen log-probability
* rejected log-probability
* policy/reference divergence
* reward margin
* response length
* training stability

---

# Evaluation

The final evaluation uses three axes.

## 1. Knowledge

**AlgerianMMLU**

Measures whether alignment preserves or improves performance on Algerian-context knowledge and reasoning tasks.

---

## 2. Preference

**Held-out preference accuracy**

The model is evaluated on preference examples that were not used during training.

For a preference pair:

[
(x,y_w,y_l)
]

the model is considered correct when:

[
\log\pi(y_w|x)

>

\log\pi(y_l|x).
]

---

## 3. Generation

**Generation win rate**

Model generations are compared against a baseline and/or competing checkpoint to estimate practical response quality.

---

# Triple-Axis Comparison

The central comparison is:

```text
                    ┌──────────────┐
                    │    Base      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     SFT      │
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
                    │     DPO      │
                    └──────────────┘
```

evaluated across:

| Model | AlgerianMMLU | Preference Accuracy | Win Rate |
| ----- | -----------: | ------------------: | -------: |
| Base  |            — |                   — |        — |
| SFT   |            — |                   — |        — |
| DPO   |            — |                   — |        — |

This makes it possible to distinguish:

* knowledge preservation
* preference alignment
* generation quality

rather than treating a single metric as evidence of improvement.

---

# Qualitative Analysis

At least **30 DPO generations** are manually inspected.

The analysis categorizes failure modes rather than only collecting anecdotes.

Example taxonomy:

```text
Failure taxonomy
├── instruction following
├── factuality
├── unnatural Darija
├── excessive code-switching
├── verbosity
├── refusal behavior
├── hallucination
├── cultural/context mismatch
└── formatting
```

The final report includes:

* failure category
* frequency
* representative examples
* Base → SFT → DPO comparison
* interpretation

---

# LLM Judge Reliability

A small additional study compares an LLM-based judge against native Darija speaker judgments.

The goal is not to treat the LLM judge as ground truth.

Instead:

```text
Native speaker judgment
          │
          ├──────────────┐
          │              │
          ▼              ▼
      human label    LLM judge
          │              │
          └──────┬───────┘
                 ▼
          agreement analysis
```

This provides evidence about whether automated evaluation is sufficiently reliable for the observed preference differences.

---

# Evidence Contract

The project is considered complete only when the major claims have corresponding evidence.

| Claim                                   | Evidence                     |
| --------------------------------------- | ---------------------------- |
| Scratch DPO is implemented correctly    | TRL numerical parity         |
| Loss implementation is correct          | `allclose(..., atol=1e-5)`   |
| Scratch training works                  | English smoke/full run       |
| DPO behavior is understood              | health + degeneration report |
| Darija preference labels are reliable   | Cohen's (\kappa), ≥100 pairs |
| SFT configuration is justified          | staged SFT sweep             |
| DPO configuration is justified          | β sweep                      |
| Alignment improves preference behavior  | held-out preference accuracy |
| Generation quality improves             | win rate                     |
| Knowledge is preserved                  | AlgerianMMLU                 |
| Failure modes are understood            | 30+ qualitative generations  |
| Automated judging is trustworthy enough | native-speaker comparison    |

---

# Execution Plan

| Week  | Focus                       | Main Evidence                     |
| ----- | --------------------------- | --------------------------------- |
| **1** | Scratch DPO mechanics       | TRL parity                        |
| **2** | Scratch training            | English run + health report       |
| **3** | Darija data + SFT           | κ + SFT sweep                     |
| **4** | Production DPO + evaluation | triple-axis evaluation + taxonomy |

### Week 1 — DPO Mechanics

```text
model/tokenizer
      ↓
preference triples
      ↓
masks
      ↓
log-probs
      ↓
reference policy
      ↓
DPO derivation
      ↓
DPO loss
      ↓
TRL allclose
```

### Week 2 — Scratch Training

```text
training loop
      ↓
English preference data
      ↓
1–2k training examples
      ↓
held-out preference evaluation
      ↓
health analysis
```

### Week 3 — Darija Pipeline

```text
resource survey
      ↓
annotation guideline
      ↓
SFT data
      ↓
preference pairs
      ↓
κ
      ↓
SFT sweep
```

### Week 4 — Production DPO

```text
selected SFT checkpoint
      ↓
TRL DPO
      ↓
β sweep
      ↓
Base / SFT / DPO
      ↓
AlgerianMMLU
      ↓
preference accuracy
      ↓
win rate
      ↓
qualitative taxonomy
```

---

# Reproducibility

Experiments are configuration-driven.

Important experimental parameters are stored under:

```text
configs/
```

Results and observations are recorded under:

```text
reports/
notes/runs.md
```

Each experiment should record:

* model
* tokenizer
* dataset/version
* random seed
* learning rate
* batch size
* gradient accumulation
* LoRA configuration
* quantization configuration
* DPO β
* number of steps/epochs
* hardware
* VRAM usage
* training speed
* evaluation results

---

# Status

## Scratch DPO

* [ ] Model/tokenizer/data contract
* [ ] Canonical preference triples
* [ ] Chat templating
* [ ] Response-only masks
* [ ] Data audit
* [ ] Log-probability primitive
* [ ] Reference policy
* [ ] DPO derivation
* [ ] DPO loss
* [ ] Degenerate/sign/numerical tests
* [ ] TRL numerical oracle
* [ ] Scratch training loop
* [ ] English DPO run
* [ ] DPO health report

## Darija Alignment

* [ ] Darija resource survey
* [ ] Preference guideline
* [ ] SFT dataset
* [ ] Preference dataset
* [ ] Double-annotation sample
* [ ] Cohen's κ
* [ ] Dataset card
* [ ] TRL SFT
* [ ] QLoRA instrumentation
* [ ] SFT target-module sweep
* [ ] SFT rank sweep
* [ ] LoRA/QLoRA comparison
* [ ] Data-fraction sweep
* [ ] Production DPO
* [ ] β sweep
* [ ] AlgerianMMLU
* [ ] Held-out preference accuracy
* [ ] Generation win rate
* [ ] 30+ generation qualitative analysis
* [ ] LLM-judge reliability study

---

# Design Principle

The project follows one rule:

> **Do not claim that the pipeline works without defining what evidence would prove it.**

The first half therefore establishes that the DPO implementation is mathematically and numerically correct.

The second half uses that verified understanding to build and evaluate an Algerian Darija alignment pipeline.

```text
Understand
    ↓
Implement
    ↓
Test
    ↓
Verify
    ↓
Train
    ↓
Measure
    ↓
Analyze
    ↓
Release
```

---

# Related Work

This project builds on established work in:

* Direct Preference Optimization (DPO)
* supervised fine-tuning
* LoRA / QLoRA
* preference learning
* Arabic and dialectal NLP
* LLM evaluation

The implementation and experimental decisions are documented in `notes/` and the corresponding reports.

---

# License

See [`LICENSE`](LICENSE).

