# Track A Data Card

## Purpose

English preference data used exclusively to validate
scratch DPO mechanics.

This dataset is not the Darija alignment dataset.

## Source

- Dataset: Anthropic/hh-rlhf
- Subset: helpful-base
- Split: train

## Canonical schema

Each example contains:

- id
- prompt
- chosen
- rejected
- source
- split
- metadata

## Model

Qwen/Qwen2.5-0.5B-Instruct

## Tokenizer

Qwen/Qwen2.5-0.5B-Instruct

## Chat template

The tokenizer's native `chat_template` is used.

No manually constructed Qwen conversation format
is used.

## Template provenance

- template_version: tokenizer.chat_template
- template_hash: SHA-256
- add_generation_prompt: true

## Tokenization

Maximum sequence length:

512 tokens.

## Truncation

The prompt is never truncated.

If a prompt exceeds 512 tokens, the example is rejected.

If the prompt fits but the complete response exceeds
the limit, response tokens are truncated.

## Loss masking

Prompt tokens:

loss_mask = 0

Response tokens:

loss_mask = 1

Padding tokens:

loss_mask = 0

## Padding

Right padding is used.

`attention_mask` identifies real tokens.

`loss_mask` identifies tokens contributing to
DPO sequence log-probabilities.

## Label audit

At least 20 examples from the smoke slice were
manually inspected.

Checked:

- chosen/rejected answer the same prompt
- chosen is actually preferable
- no empty responses
- no identical responses
- no obvious corrupted examples

## Limitations

The English preference data is used only as a
mechanics-validation dataset.

It does not establish anything about Darija alignment.