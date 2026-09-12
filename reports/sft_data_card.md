# Algerian Darija SFT Dataset Card

## 1. Summary

This dataset is an instruction-tuning dataset for adapting
Qwen2.5-1.5B-Instruct to Algerian Darija.

The dataset is designed to provide high-quality Algerian Darija
instruction-response examples across multiple task categories.

## 2. Intended use

The dataset is intended for:

- supervised fine-tuning (SFT)
- Algerian Darija instruction following
- subsequent preference optimization experiments
- research on low-resource dialect adaptation

It is not intended to be used as an evaluation dataset.

## 3. Language and dialect

Primary language:

- Algerian Darija

Scripts:

- Arabic
- Arabizi
- Mixed Arabic/Latin script

Code-switching with French, English, or MSA is allowed when
natural or useful for the task.

## 4. Dataset schema

Each JSONL record contains:

- `id`
- `messages`
- `category`
- `script`
- `source`
- `license`
- `metadata`

The `messages` field contains a user message followed by an
assistant response.

## 5. Task categories

The dataset may contain:

- education
- general QA
- reasoning
- daily life
- Algerian culture
- commerce
- translation
- code-switching
- technical
- safety
- humor

## 6. Provenance

Each example contains source and license metadata.

Original project-created examples are marked with:

`source: original`

and:

`license: project-created`

External resources will only be included after their licensing
and provenance have been reviewed.

## 7. Quality control

The dataset is checked for:

- valid JSONL
- required fields
- unique IDs
- duplicate examples
- valid categories
- valid script labels
- non-empty messages
- valid message roles
- Algerian Darija dialect metadata
- reasonable example length

A separate validation script is provided at:

`scripts/validate_sft_data.py`

## 8. Chat-template formatting

Examples are stored as structured `messages` rather than manually
formatted model tokens.

For Qwen2.5-1.5B-Instruct, formatting is performed using the
tokenizer's native chat template:

`tokenizer.apply_chat_template(...)`

This ensures that SFT formatting is consistent with the base model.

## 9. Train/validation split

The dataset is split into training and validation subsets using
a deterministic random seed.

Seed:

`42`

The validation ratio is:

`20%`

The split is performed by:

`scripts/split_sft_data.py`

## 10. Evaluation separation

Evaluation datasets such as DziriEval must not be included in
the SFT training data.

Evaluation examples are kept separate to avoid contamination.

## 11. Current development status

The current repository version contains a small smoke-test dataset
used to validate the data pipeline.

It is not yet the final training dataset.

The production dataset will be expanded only after the schema,
quality checks, provenance tracking, splitting, and formatting
pipeline have been validated.

## 12. Limitations

Potential limitations include:

- limited coverage of Algerian regional variation
- variation between Arabic and Latin/Arabizi writing
- code-switching variability
- possible cultural and linguistic annotation bias
- limited representation of some domains

These limitations will be documented and reassessed as the dataset
grows.
