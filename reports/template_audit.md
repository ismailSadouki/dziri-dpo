# Template Audit

## Model

`Qwen/Qwen2.5-0.5B-Instruct`

## Tokenizer

`Qwen/Qwen2.5-0.5B-Instruct`

## Template policy

The tokenizer's native `chat_template` is the single source of truth.

No manual Qwen chat formatting is used.

Chosen and rejected responses use:

- the same tokenizer
- the same chat template
- the same prompt
- the same role structure

The only intended difference is the assistant response.

## Template provenance

- `template_version`: `tokenizer.chat_template`
- `template_hash`: `cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f`
- `hash_algorithm`: `SHA-256`

## Truncation policy

The prompt is preserved.

If the combined sequence exceeds `max_length=512`, response
tokens are truncated rather than prompt tokens.

The exact tokenization/truncation implementation will be handled
in the subsequent tokenization milestone.

## Audit example

### Raw example

**ID:** `tiny_001`

**Prompt:**

```text
What is 2 + 2?
```
Chosen:
```text
2 + 2 equals 4.
```
Rejected:

```text
2 + 2 equals 5.
```

Prompt-only rendering

```text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
What is 2 + 2?<|im_end|>
<|im_start|>assistant

```

Chosen rendering
```text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
What is 2 + 2?<|im_end|>
<|im_start|>assistant
2 + 2 equals 4.<|im_end|>

```

Rejected rendering

```text
<|im_start|>system
You are Qwen, created by Alibaba Cloud. You are a helpful assistant.<|im_end|>
<|im_start|>user
What is 2 + 2?<|im_end|>
<|im_start|>assistant
2 + 2 equals 5.<|im_end|>

```

Validation
- Prompt-only rendering generated: YES
- Chosen rendering generated: YES
- Rejected rendering generated: YES
- Chosen starts with identical prompt prefix: YES
- Rejected starts with identical prompt prefix: YES
- Chosen/rejected use the same template: YES
- Manual template modifications: NO

Processed metadata

```text
{
  "model": "Qwen/Qwen2.5-0.5B-Instruct",
  "tokenizer": "Qwen/Qwen2.5-0.5B-Instruct",
  "template_version": "tokenizer.chat_template",
  "template_hash": "cd8e9439f0570856fd70470bf8889ebd8b5d1107207f67a5efb46e342330527f",
  "template_hash_algorithm": "sha256",
  "add_generation_prompt": true,
  "truncation_policy": "preserve_prompt_truncate_response",
  "max_length": 512
}
```
