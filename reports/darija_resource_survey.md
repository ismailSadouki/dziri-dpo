# Algerian Darija Resource Survey

## 1. Objective

The purpose of this survey is to identify existing resources relevant to
Algerian Darija NLP and determine:

1. what can be reused;
2. what can only be used as related work or evaluation;
3. what requires additional provenance/licensing verification;
4. what research gap remains for the DziriDPO project.

The survey distinguishes between:

- models;
- raw/unstructured corpora;
- instruction datasets;
- preference datasets;
- evaluation datasets;
- Arabic/Maghrebi resources.


---

# 2. Models

## 2.1 Qwen2.5-1.5B-Instruct

Language/resource type:
- multilingual instruction model
- Arabic-capable
- Qwen2 architecture

Role in DziriDPO:

**PRIMARY BASE MODEL**

Reason:

- suitable scale for QLoRA;
- native chat template;
- Arabic capability;
- clean baseline for measuring Algerian-Darija adaptation;
- continuity with Track A Qwen experiments.

The model is not assumed to be Algerian-Darija-specialized.

---

## 2.2 Atlas-Chat

Resource:

`MBZUAI-Paris/Atlas-Chat-2B`

Language:

Moroccan Arabic / Moroccan Darija.

Role:

**RELATED WORK / SECONDARY COMPARATIVE BASELINE**

Atlas-Chat is important because it demonstrates a complete low-resource
Darija adaptation pipeline. The authors construct an instruction mixture
by consolidating existing Darija resources, creating new data manually and
synthetically, and translating English instructions with quality control.

Atlas also introduces DarijaMMLU.

Atlas should NOT be treated as an Algerian-Darija training resource.

The Moroccan-Darija data cannot simply be relabeled as Algerian Darija.

Potential future role:

- methodological comparison;
- cross-Maghreb baseline;
- analysis of transfer from Moroccan Darija to Algerian Darija.

---

# 3. Algerian Darija corpora

## 3.1 DarijaDZ

Resource:

`nasrellahkharroubi/DarijaDz`

Type:

Large-scale Algerian YouTube-comment corpus.

Reported scale:

- approximately 13.4M documents;
- approximately 174M word-level tokens.

Characteristics:

- Algerian Darija;
- Arabic script;
- Latin/Arabizi;
- mixed-script content;
- informal online language;
- code-switching.

Potential usefulness:

- corpus analysis;
- language-model pretraining;
- continued pretraining;
- tokenizer analysis;
- dialect/orthography analysis.

Decision:



The current public dataset documentation does not provide a sufficiently
clear underlying-content licensing/provenance basis for us to assume that
the YouTube-derived material can be redistributed or incorporated into a
new public training dataset.

It may be studied as a resource, but legal/provenance status must be
resolved before training or redistribution.

---

## 3.2 Algerian Darja Corpus

Resource:

`touati-kamel/algerian-darja-corpus`

Reported scale:

- 10,022 transcript documents;
- approximately 32.9M words.

Characteristics:

- conversational Algerian Darja;
- Arabic script;
- Latin/Arabizi;
- French/English code-switching;
- podcast and talk-show transcripts.

Reported license:

CC-BY-4.0.

Potential usefulness:

- Algerian language analysis;
- corpus statistics;
- orthographic/code-switching analysis;
- possible controlled SFT source after provenance verification.

Decision:


The dataset license is useful, but the underlying YouTube-source rights and
the distinction between dataset-license rights and source-content rights
must be documented before redistribution or model release.

---

## 3.3 DarjaCore/algerian-darja-sample

Resource:

`DarjaCore/algerian-darja-sample`

Reported scale:

- 1,220,346 text samples;
- 5.49M words;
- 50.66 MB.

Characteristics:

- Algerian Darija;
- predominantly Arabic script;
- some Latin/Arabizi;
- emojis and informal text.

Potential usefulness:

- corpus analysis;
- language modeling;
- orthographic analysis.

Decision:

LICENSE/PROVENANCE AUDIT REQUIRED


---

# 4. Algerian instruction/task resources

## 4.1 Algerian Darija instruction resources

HF currently contains several datasets tagged for Algerian Darija,
including task-specific and instruction-like resources.

These will be individually audited rather than merged automatically.

For every candidate we will record:

- original source;
- creator;
- collection method;
- human vs synthetic generation;
- license;
- fields;
- language/script;
- duplication risk;
- contamination risk;
- suitability for SFT.

Decision:

**INDIVIDUAL AUDIT REQUIRED**

---

# 5. Preference datasets

## 5.1 DziriAlign

Resource:

`touati-kamel/DziriAlign`

Reported size:

1,000 preference examples.

Schema:

- `prompt`
- `chosen`
- `rejected`

Coverage includes:

- Algerian market negotiation;
- socio-linguistic interaction;
- sociocultural scenarios;
- Algerian humor.

Reported license:

MIT.

Role:

**EXTERNAL PREFERENCE RESOURCE / COMPARISON**

Important:

DziriAlign means the DziriDPO project must NOT claim to create the first
Algerian-Darija preference dataset.

The project's contribution should instead focus on:

- provenance-controlled data construction;
- explicit annotation criteria;
- human preference annotation;
- double annotation;
- inter-annotator agreement;
- disagreement analysis;
- controlled SFT → DPO comparison;
- evaluation of linguistic and cultural alignment;
- reliability/failure analysis.


**DziriAlign: important methodological limitation**

DziriAlign contains 1,000 Algerian-Darija preference pairs. Inspection of
the released examples shows that the preferred responses are generally
Algerian Darija, while many rejected responses are in MSA or English, or
are deliberately formal/robotic.

This means that a substantial part of the preference signal may correspond
to dialect/style selection rather than fine-grained preference between two
plausible Algerian-Darija responses.

The public dataset card does not provide enough detail about the generation
and annotation procedure to establish that the rejected responses were
independently human-generated and that the pairwise preference was obtained
through controlled human annotation.

Therefore, DziriAlign is treated as a related alignment resource and
methodological comparison, not as a source for the project's DPO training
data.



---

# 6. Evaluation resources

## 6.1 DziriEval

Resource:

`touati-kamel/DziriEval`

Reported size:

1,000 multiple-choice questions.

Characteristics:

- native Algerian Darija;
- Algerian cultural knowledge;
- reasoning;
- everyday commerce;
- language/lexical phenomena;
- code-switching;
- Arabizi.

Reported license:

MIT.

Decision:

**PRIMARY EXTERNAL EVALUATION CANDIDATE**

It should not be used for SFT or DPO training.

Its evaluation examples must remain held out from training.

---

## 6.2 ArabicMMLU

ArabicMMLU contains 14,575 multiple-choice questions over 40 tasks.

The benchmark is primarily in Modern Standard Arabic rather than Algerian
Darija.

Decision:

**SECONDARY ARABIC EVALUATION REFERENCE**

Useful for measuring whether adaptation to Algerian Darija causes unexpected
changes in broader Arabic capabilities.

Not an Algerian-Darija benchmark.

---

## 6.3 DarijaMMLU

DarijaMMLU was introduced as part of Atlas-Chat.

Language:

Moroccan Darija.

Decision:

**RELATED WORK / CROSS-DIALECT REFERENCE**

It should not be treated as an Algerian benchmark.

It is useful for understanding how a low-resource dialect-specific
evaluation suite can be constructed.

---

## 6.4 AlgerianMMLU

Status:

No established AlgerianMMLU benchmark has been identified as a mature,
standard resource comparable to ArabicMMLU or Atlas's DarijaMMLU.

Decision:

**NOT A PREREQUISITE**

AlgerianMMLU may become a future research contribution, but DziriDPO will
not depend on its prior existence.

The project will instead use existing Algerian evaluation resources plus
a controlled held-out evaluation set.

---

# 7. Research gap

The survey does NOT support the claim that Algerian Darija has no public
resources.

Instead, the ecosystem is fragmented across:

- large raw corpora;
- conversational corpora;
- task-specific datasets;
- instruction resources;
- preference data;
- evaluation benchmarks.

The main gap relevant to DziriDPO is therefore methodological and
experimental rather than simply the absence of data.

The project aims to provide a reproducible pipeline:

Algerian Darija data
→ controlled SFT
→ human preference annotation
→ DPO
→ held-out evaluation
→ preference/reliability analysis.

The contribution should emphasize provenance, annotation quality,
controlled experimentation, and evaluation rather than claiming to be the
first Algerian Darija dataset.

---

# 8. Preliminary source decision

### SFT

Potential sources:

- controlled Algerian instruction/task datasets;
- selected permissively licensed Algerian conversational resources after
  provenance verification;
- newly created Algerian Darija instruction data.

We will not automatically use:

- raw YouTube corpora with unclear redistribution rights;
- Moroccan Darija resources;
- evaluation benchmarks.

### Preference training

Primary plan:

**We will Create a new human-annotated preference dataset.**

External DziriAlign is treated as a resource for comparison/audit, not as
an automatic component of our training set.

### Evaluation

We will use:

- DziriEval where appropriate;
- additional held-out Algerian Darija evaluation data;
- ArabicMMLU as a secondary Arabic reference;
- potentially a future AlgerianMMLU-style benchmark.

---

# 9. Open provenance questions

Before any external dataset is added to training, We should verify:

1. Who originally created the data?
2. What is the original source?
3. How was it collected?
4. Is the dataset license explicit?
5. Does the license permit the intended use?
6. Does the license permit redistribution?
7. Are underlying third-party copyrights relevant?
8. Is personal information present?
9. Is the dataset synthetic or human-generated?
10. Could the dataset overlap with evaluation data?
11. Could it contaminate the preference benchmark?
12. Can we cite the original source correctly?

A resource remains **HOLD** until these questions are sufficiently
answered.