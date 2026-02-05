import json

from conftest import make_record
from tokentally.aggregate import group, total
from tokentally.export import to_json


def test_json_has_rows_and_total() -> None:
    records = [make_record(model="claude-haiku-4-5", input_tokens=1_000_000)]
    doc = json.loads(to_json(group(records, "model"), "model", total(records)))
    assert doc["rows"][0]["model"] == "claude-haiku-4-5"
    assert doc["rows"][0]["cost"] == 1.0
    assert doc["total"]["total_tokens"] == 1_000_000
