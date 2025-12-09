from datetime import timezone
from pathlib import Path

from tokentally.parsers._util import iter_jsonl, parse_timestamp


def test_iter_jsonl_skips_blank_broken_and_non_object_lines(tmp_path: Path) -> None:
    f = tmp_path / "log.jsonl"
    f.write_text('{"a": 1}\n\n[1, 2]\n{"b": 2\n{"c": 3}\n', encoding="utf-8")
    assert list(iter_jsonl(f)) == [{"a": 1}, {"c": 3}]


def test_parse_timestamp_handles_z_suffix() -> None:
    ts = parse_timestamp("2026-03-04T05:06:07.123Z")
    assert ts.tzinfo is not None
    assert ts.utcoffset() == timezone.utc.utcoffset(None)
    assert (ts.year, ts.month, ts.day, ts.hour) == (2026, 3, 4, 5)


def test_parse_timestamp_assumes_utc_for_naive_values() -> None:
    assert parse_timestamp("2026-03-04T05:06:07").tzinfo == timezone.utc
