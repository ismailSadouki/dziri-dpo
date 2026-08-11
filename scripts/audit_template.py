import hashlib
import json

from pathlib import Path



from transformers import AutoTokenizer




MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"
FIXTURE_PATH = Path("tests/fixtures/tiny_preferences.jsonl")
REPORT_PATH = Path("reports/template_audit.md")

def load_first_example():
    line = next(
    (line for line in FIXTURE_PATH.read_text().splitlines() if line.strip()),
    None
    )
    return json.loads(line)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True
    )

    if tokenizer.chat_template is None:
        raise RuntimeError(
            f"{MODEL_NAME} does not provide a chat template"
        )
    template = tokenizer.chat_template 
    template_hash = sha256_text(template)

    example = load_first_example()

    prompt_messages = [
        {
            "role": "user",
            "content": example["prompt"]
        }
    ]

    chosen_messages = [
        {
            "role": "user",
            "content": example["prompt"]
        },
        {
            "role": "assistant",
            "content": example["chosen"]
        }
    ]

    rejected_messages = [
        {
        "role": "user",
        "content": example["prompt"]
        },
        {
            "role": "assistant",
            "content": example["rejected"]
        }
    ]

    
    # Prompt presented to the model before generation
    prompt_rendered = tokenizer.apply_chat_template(
        prompt_messages,
        tokenize=False,
        add_generation_prompt=True
    )
    # Complete chosen/rejected conversations.
    chosen_rendered = tokenizer.apply_chat_template(
        chosen_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    rejected_rendered = tokenizer.apply_chat_template(
        rejected_messages,
        tokenize=False,
        add_generation_prompt=False,
    )

    # The chosen and rejected conversations should share exactly the same rendered prompt prefix.
    if not chosen_rendered.startswith(prompt_rendered):
        raise AssertionError(
            "Chosen rendering does not start with the prompt rendering."
        )
    if not rejected_rendered.startswith(prompt_rendered):
        raise AssertionError(
            "Rejected rendering does not start with the prompt rendering."
        )

    # Record provenance in processed metadata.
    processed_metadata = {
        "model": MODEL_NAME,
        "tokenizer": MODEL_NAME,
        "template_version": "tokenizer.chat_template",
        "template_hash": template_hash,
        "template_hash_algorithm": "sha256",
        "add_generation_prompt": True,
        "truncation_policy": "preserve_prompt_truncate_response",
        "max_length": 512
    }

    report = f"""# Template Audit

## Model

`{MODEL_NAME}`

## Tokenizer

`{MODEL_NAME}`

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

- `template_version`: `{processed_metadata["template_version"]}`
- `template_hash`: `{template_hash}`
- `hash_algorithm`: `SHA-256`

## Truncation policy

The prompt is preserved.

If the combined sequence exceeds `max_length=512`, response
tokens are truncated rather than prompt tokens.

The exact tokenization/truncation implementation will be handled
in the subsequent tokenization milestone.

## Audit example

### Raw example

**ID:** `{example["id"]}`

**Prompt:**

```text
{example["prompt"]}
```
Chosen:
```text
{example["chosen"]}
```
Rejected:

```text
{example["rejected"]}
```

Prompt-only rendering

```text
{prompt_rendered}
```

Chosen rendering
```text
{chosen_rendered}
```

Rejected rendering

```text
{rejected_rendered}
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
{json.dumps(processed_metadata, indent=2)}
```
"""
    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(report, encoding="utf-8")

    print(f"Model:          {MODEL_NAME}")
    print(f"Template hash:  {template_hash}")
    print(f"Report written: {REPORT_PATH}")

if __name__ == "__main__":
     main()

