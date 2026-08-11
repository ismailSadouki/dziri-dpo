### M1.1 — Model, tokenizer, chat-template contract

Track A freezes the following contract:

- Model: `Qwen/Qwen2.5-0.5B-Instruct`
- Tokenizer: matching Qwen tokenizer
- Chat template: tokenizer-native template
- Manual template formatting: disabled
- Preference schema: `(prompt, chosen, rejected)`
- Maximum sequence length: `512`
- Truncation: preserve prompt, truncate response
- Template provenance: SHA-256 hash of `tokenizer.chat_template`

Run the M1.1 checks with:

```bash
pytest -q tests/test_schema.py tests/test_template_audit.py
```

Generate the rendered template audit with:

```bash
python scripts/audit_template.py
```
TRL is not used to implement the Track A mechanics. It will only
serve as a numerical correctness oracle later.