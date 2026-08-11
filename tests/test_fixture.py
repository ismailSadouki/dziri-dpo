def test_tiny_preference_fixture():
    from pathlib import Path
    import json

    path = Path("tests/fixtures/tiny_preferences.jsonl")

    rows = [
        json.loads(line)
        for line in path.read_text().splitlines()
        if line.strip()
    ]

    assert len(rows) == 3

    required_fields = {
        "id",
        "prompt",
        "chosen",
        "rejected",
        "source",
        "split",
        "metadata",
    }

    for row in rows:
        assert required_fields.issubset(row.keys())

        assert row["id"]
        assert row["prompt"]
        assert row["chosen"]
        assert row["rejected"]
        assert row["source"]
        assert row["split"]
        assert isinstance(row["metadata"], dict)