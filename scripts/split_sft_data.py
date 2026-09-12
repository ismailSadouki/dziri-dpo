import json
import random
from pathlib import Path

INPUT_PATH = Path("data/instruction_dataset.jsonl")
TRAIN_PATH = Path("data/splits/train.jsonl")
VAL_PATH = Path("data/splits/val.jsonl")

SEED = 42
VAL_RATIO = 0.2


def main():
    with INPUT_PATH.open(encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]

    rng = random.Random(SEED)
    rng.shuffle(rows)

    val_size = max(1, round(len(rows) * VAL_RATIO))

    val_rows = rows[:val_size]
    train_rows = rows[val_size:]

    TRAIN_PATH.parent.mkdir(parents=True, exist_ok=True)

    with TRAIN_PATH.open("w", encoding="utf-8") as f:
        for row in train_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    with VAL_PATH.open("w", encoding="utf-8") as f:
        for row in val_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    print("SFT SPLIT: PASS")
    print(f"Total: {len(rows)}")
    print(f"Train: {len(train_rows)}")
    print(f"Validation: {len(val_rows)}")
    print(f"Seed: {SEED}")


if __name__ == "__main__":
    main()