
# M0A decisions

- **Model**: `Qwen/Qwen2.5-0.5B-Instruct` (instruction-tuned)

Why:

- only 0.49B parameters
- Apache-2.0 license
- already instruction-tuned
- has an official chat template
- 24 layers, 14 Q heads / 2 KV heads
- small enough for fast iteration


- **Preference source**: `Anthropic/hh-rlhf`, specifically `helpful-base`.

It is a human preference dataset with chosen/rejected responses, and the Hugging Face release provides a `helpful-base` split with train/test files. It is MIT licensed.

For scratch debugging, we do not download the whole dataset into the repo. We later take a deterministic small slice.
