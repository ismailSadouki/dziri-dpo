# B0 Model Decision — Track B

## Decision

**Primary production model:** `Qwen/Qwen2.5-1.5B-Instruct`

**Secondary candidate:** `MBZUAI-Paris/Atlas-Chat-2B`

The Track B production pipeline will use Qwen2.5-1.5B-Instruct as the
primary base model for Algerian Darija SFT and DPO experiments.

Atlas-Chat-2B is retained as a secondary comparative candidate and is not
used as the primary model for the initial pipeline.

---

## Selection criteria

The models were evaluated using the following criteria:

1. Relevance to Algerian Darija
2. Arabic/multilingual capability
3. Instruction-following capability
4. Chat-template support
5. Parameter/computational requirements
6. License suitability
7. Compatibility with LoRA/QLoRA
8. Continuity with Track A
9. Suitability for controlled SFT → DPO experiments

---

## Primary model: Qwen2.5-1.5B-Instruct

### Reasons for selection

### 1. Multilingual and Arabic capability

Qwen2.5-1.5B-Instruct is a multilingual instruction model with Arabic
support. This makes it a suitable starting point for adaptation to
Algerian Darija without requiring a model that was already specialized
for a different Maghrebi dialect.

### 2. Appropriate model scale

The 1.5B model provides a useful compromise between model capacity and
available compute.

The local research environment has an NVIDIA RTX 3050 Laptop GPU with
approximately 3.68 GiB VRAM. Initial 4-bit loading successfully completed
on this hardware.

### 3. Native instruction/chat interface

The tokenizer provides a chat template, allowing the SFT and DPO
experiments to use the model's intended conversational formatting.

The B0 smoke test confirmed:

- tokenizer loading
- chat-template availability
- prompt tokenization
- generation

### 4. Compatibility with the existing Track A work

Track A already used the Qwen2.5-Instruct family.

Using Qwen2.5-1.5B-Instruct for Track B therefore preserves methodological
continuity while increasing model capacity.

Track A and Track B should nevertheless be treated as separate
experimental tracks.

### 5. Efficient adaptation

The model is compatible with the planned PEFT/LoRA and 4-bit QLoRA
pipeline.

The initial B0 configuration uses:

- 4-bit NF4 quantization
- double quantization
- BF16 computation
- LoRA rank 16
- LoRA alpha 32
- LoRA dropout 0.05
- `q_proj`, `k_proj`, `v_proj`, `o_proj` target modules

These are baseline engineering choices and will be evaluated later rather
than treated as optimal hyperparameters.

### 6. Licensing

The model is distributed under the Apache-2.0 license according to its
model documentation.

The exact license and model revision used for each experiment will be
recorded in experiment metadata.

---

## Secondary candidate: Atlas-Chat-2B

`MBZUAI-Paris/Atlas-Chat-2B` is retained as a secondary candidate.

### Why it is interesting

Atlas-Chat-2B is particularly relevant because it was developed with
Moroccan Darija in mind.

This makes it an interesting cross-Maghreb comparison point.

### Why it is not the primary model

The main research target is **Algerian Darija**, not Moroccan Darija.

Using an already Moroccan-Darija-adapted model as the primary model would
make it harder to separate:

- general multilingual transfer,
- Maghrebi dialect transfer,
- existing Moroccan-Darija specialization,
- and adaptation obtained from our Algerian Darija data.

Qwen therefore provides a cleaner primary starting point for studying
Algerian Darija adaptation.

Atlas may become valuable later as a comparative baseline if resources
and compute permit.

---

## B0 validation evidence

### Local hardware

- GPU: NVIDIA GeForce RTX 3050 Laptop GPU
- VRAM: 3.68 GiB
- CUDA: 12.8
- BF16 support: yes

### Qwen smoke test

Model:

`Qwen/Qwen2.5-1.5B-Instruct`

Observed architecture:

- Model class: `Qwen2ForCausalLM`
- Model type: `qwen2`
- Hidden size: 1536
- Layers: 28
- Attention heads: 12
- Key/value heads: 2
- Vocabulary size: 151936

Tokenizer:

- Vocabulary reported by tokenizer: 151665
- Chat template: available

### Quantized loading

The model successfully loaded using:

- 4-bit quantization
- NF4
- double quantization
- BF16 compute

### Generation

A generation smoke test using an Algerian Darija prompt completed
successfully.

Peak GPU memory observed during the smoke test:

- Allocated: 1.09 GiB
- Reserved: 1.12 GiB

This validates basic inference feasibility on the local RTX 3050.

---

## Important parameter-count note

The loaded quantized model reported:

`888,616,448` parameters through the runtime parameter-counting
procedure.

This value should **not** be interpreted as the official parameter count
of the Qwen2.5-1.5B checkpoint because parameters loaded through the
quantization/runtime representation do not necessarily provide a reliable
checkpoint-level parameter count.

The experiment documentation should therefore use the model's official
checkpoint specification when describing model size and should separately
record runtime/quantization information.

---

## Decision

For the initial Track B production pipeline:

**Qwen2.5-1.5B-Instruct → SFT → DPO**

is the selected path.

Atlas-Chat-2B remains a possible secondary comparative experiment.
