import json
import random
from collections import defaultdict
from pathlib import Path


INPUT_PATH = Path("data/instruction_dataset_v1.jsonl")
TRAIN_PATH = Path("data/splits/train.jsonl")
VAL_PATH = Path("data/splits/val.jsonl")

SEED = 42
VAL_RATIO = 0.2


def load_dataset():
    with INPUT_PATH.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def stratified_split(rows):
    by_category = defaultdict(list)

    for row in rows:
        category = row["category"]
        by_category[category].append(row)

    rng = random.Random(SEED)

    train_rows = []
    val_rows = []

    for category in sorted(by_category):
        category_rows = by_category[category].copy()
        rng.shuffle(category_rows)

        val_size = max(1, round(len(category_rows) * VAL_RATIO))

        val_rows.extend(category_rows[:val_size])
        train_rows.extend(category_rows[val_size:])

    rng.shuffle(train_rows)
    rng.shuffle(val_rows)

    return train_rows, val_rows


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def main():
    rows = load_dataset()

    train_rows, val_rows = stratified_split(rows)

    write_jsonl(TRAIN_PATH, train_rows)
    write_jsonl(VAL_PATH, val_rows)

    print("SFT SPLIT: PASS")
    print(f"Input: {INPUT_PATH}")
    print(f"Total: {len(rows)}")
    print(f"Train: {len(train_rows)}")
    print(f"Validation: {len(val_rows)}")
    print(f"Seed: {SEED}")
    print(f"Validation ratio: {VAL_RATIO}")


if __name__ == "__main__":
    main()