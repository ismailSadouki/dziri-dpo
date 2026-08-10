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

    for row in rows:
        assert set(row) == {"prompt", "chosen", "rejected"}
        assert row["prompt"]
        assert row["chosen"]
        assert row["rejected"]