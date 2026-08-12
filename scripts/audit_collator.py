import json
from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from transformers import AutoTokenizer

from scratch_dpo.collator import DPODataCollator
from scratch_dpo.data import tokenize_pair


MODEL_NAME = "Qwen/Qwen2.5-0.5B-Instruct"

FIXTURE_PATH = Path(
    "tests/fixtures/tiny_preferences.jsonl"
)

REPORT_PATH = Path(
    "reports/collated_batch_audit.md"
)

MAX_LENGTH = 512


def load_examples():
    rows = []

    for line in FIXTURE_PATH.read_text(
        encoding="utf-8"
    ).splitlines():
        if line.strip():
            rows.append(json.loads(line))

    return rows


def token_region(
    attention: int,
    loss_mask: int,
) -> str:
    if attention == 0:
        return "PAD"

    if loss_mask == 1:
        return "R"

    return "P"


def decode_batch(
    tokenizer,
    input_ids,
    attention_mask,
    loss_mask,
):
    lines = []

    for position, (
        token_id,
        attention,
        loss,
    ) in enumerate(
        zip(
            input_ids,
            attention_mask,
            loss_mask,
        )
    ):
        token_text = tokenizer.decode(
            [token_id],
            skip_special_tokens=False,
        )

        token_text = (
            token_text
            .replace("\n", "\\n")
            .replace("\t", "\\t")
        )

        region = token_region(
            int(attention),
            int(loss),
        )

        lines.append(
            f"{position:04d} | "
            f"{region:3s} | "
            f"{token_id:6d} | "
            f"{token_text!r}"
        )

    return "\n".join(lines)


def validate_batch(batch):
    required = {
        "chosen_input_ids",
        "chosen_attention_mask",
        "chosen_loss_mask",
        "rejected_input_ids",
        "rejected_attention_mask",
        "rejected_loss_mask",
    }

    assert required.issubset(batch.keys())

    chosen_ids = batch["chosen_input_ids"]
    chosen_attention = batch["chosen_attention_mask"]
    chosen_loss = batch["chosen_loss_mask"]

    rejected_ids = batch["rejected_input_ids"]
    rejected_attention = batch["rejected_attention_mask"]
    rejected_loss = batch["rejected_loss_mask"]

    # All tensors must have the same shape within
    # their chosen/rejected branches.
    assert chosen_ids.shape == chosen_attention.shape
    assert chosen_ids.shape == chosen_loss.shape

    assert rejected_ids.shape == rejected_attention.shape
    assert rejected_ids.shape == rejected_loss.shape

    # Chosen and rejected must have a shared padded
    # sequence length.
    assert chosen_ids.shape[1] == rejected_ids.shape[1]

    # Padding must never contribute to the loss.
    assert (
        chosen_loss[chosen_attention == 0] == 0
    ).all()

    assert (
        rejected_loss[rejected_attention == 0] == 0
    ).all()

    # Loss mask can only contain 0 or 1.
    assert set(chosen_loss.unique().tolist()) <= {0, 1}
    assert set(rejected_loss.unique().tolist()) <= {0, 1}

    # Attention mask can only contain 0 or 1.
    assert set(
        chosen_attention.unique().tolist()
    ) <= {0, 1}

    assert set(
        rejected_attention.unique().tolist()
    ) <= {0, 1}


def main():
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME,
        use_fast=True,
    )

    if tokenizer.pad_token_id is None:
        raise RuntimeError(
            "Tokenizer has no pad_token_id."
        )

    tokenizer.padding_side = "right"

    raw_examples = load_examples()

    tokenized_examples = [
        tokenize_pair(
            tokenizer=tokenizer,
            prompt=row["prompt"],
            chosen=row["chosen"],
            rejected=row["rejected"],
            max_length=MAX_LENGTH,
        )
        for row in raw_examples
    ]

    collator = DPODataCollator(
        pad_token_id=tokenizer.pad_token_id
    )

    batch = collator(tokenized_examples)

    validate_batch(batch)

    lines = [
        "# Collated Batch Audit",
        "",
        f"Model: `{MODEL_NAME}`",
        "",
        f"Batch size: `{len(raw_examples)}`",
        "",
        f"Chosen shape: `{tuple(batch['chosen_input_ids'].shape)}`",
        "",
        f"Rejected shape: "
        f"`{tuple(batch['rejected_input_ids'].shape)}`",
        "",
        f"Padding token ID: `{tokenizer.pad_token_id}`",
        "",
        "## Mask semantics",
        "",
        "- `P` = prompt token, loss mask = 0",
        "- `R` = response token, loss mask = 1",
        "- `PAD` = padding token, attention mask = 0, loss mask = 0",
        "",
        "## Invariants",
        "",
        "- Chosen and rejected have the same padded length.",
        "- Attention masks contain only 0/1.",
        "- Loss masks contain only 0/1.",
        "- Padding positions have loss mask = 0.",
        "",
    ]

    for index, row in enumerate(raw_examples):

        lines.extend([
            f"## Example {index + 1}: `{row['id']}`",
            "",
            "### Chosen",
            "",
            "```text",
            decode_batch(
                tokenizer,
                batch["chosen_input_ids"][index].tolist(),
                batch["chosen_attention_mask"][index].tolist(),
                batch["chosen_loss_mask"][index].tolist(),
            ),
            "```",
            "",
            "### Rejected",
            "",
            "```text",
            decode_batch(
                tokenizer,
                batch["rejected_input_ids"][index].tolist(),
                batch["rejected_attention_mask"][index].tolist(),
                batch["rejected_loss_mask"][index].tolist(),
            ),
            "```",
            "",
        ])

    REPORT_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    REPORT_PATH.write_text(
        "\n".join(lines),
        encoding="utf-8",
    )

    print(
        f"Collator audit written to {REPORT_PATH}"
    )


if __name__ == "__main__":
    main()