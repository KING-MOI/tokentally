import json

from tokentally.aggregate import group, total
from tokentally.export import to_json

from conftest import make_record


def test_json_has_rows_and_total() -> None:
    records = [make_record(model="claude-haiku-4-5", input_tokens=1_000_000)]
    doc = json.loads(to_json(group(records, "model"), "model", total(records)))
    assert doc["rows"][0]["model"] == "claude-haiku-4-5"
    assert doc["rows"][0]["cost"] == 1.0
    assert doc["total"]["total_tokens"] == 1_000_000


def test_csv_quotes_awkward_keys() -> None:
    from tokentally.export import to_csv

    records = [make_record(project='we,ird "name"', output_tokens=3)]
    text = to_csv(group(records, "project"), "project")
    lines = text.splitlines()
    assert lines[0].startswith("project,input_tokens,")
    assert lines[1].startswith('"we,ird ""name""",0,3,')


def test_records_jsonl() -> None:
    from tokentally.export import records_jsonl
    from tokentally.pricing import PRICES

    (line,) = records_jsonl([make_record(output_tokens=1_000_000)], PRICES)
    doc = json.loads(line)
    assert doc["timestamp"] == "2026-03-01T12:00:00+00:00"
    assert doc["cost"] == 15.0
