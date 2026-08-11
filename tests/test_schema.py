import json

from pathlib import Path
import sys

sys.path.append(str(Path(__file__).resolve().parent.parent))

from scratch_dpo.schema import PreferenceExample


FIXTURE = Path("tests/fixtures/tiny_preferences.jsonl")


def test_tiny_fixture_matches_schema():
    rows = [
        json.loads(line)
        for line in FIXTURE.read_text().splitlines()
        if line.strip()
    ]

    assert len(rows) == 3

    required = {
        "id",
        "prompt",
        "chosen",
        "rejected",
        "source",
        "split",
        "metadata",
    }

    for row in rows:
        assert set(row) == required

        example = PreferenceExample(**row)
        example.validate()