from datetime import UTC
from pathlib import Path

from tokentally.parsers._util import iter_jsonl, parse_timestamp


def test_iter_jsonl_skips_blank_broken_and_non_object_lines(tmp_path: Path) -> None:
    f = tmp_path / "log.jsonl"
    f.write_text('{"a": 1}\n\n[1, 2]\n{"b": 2\n{"c": 3}\n', encoding="utf-8")
    assert list(iter_jsonl(f)) == [{"a": 1}, {"c": 3}]


def test_parse_timestamp_handles_z_suffix() -> None:
    ts = parse_timestamp("2026-03-04T05:06:07.123Z")
    assert ts.tzinfo is not None
    assert ts.utcoffset() == UTC.utcoffset(None)
    assert (ts.year, ts.month, ts.day, ts.hour) == (2026, 3, 4, 5)


def test_parse_timestamp_assumes_utc_for_naive_values() -> None:
    assert parse_timestamp("2026-03-04T05:06:07").tzinfo == UTC


def test_as_int_treats_null_bool_and_negative_as_zero() -> None:
    from tokentally.parsers._util import as_int

    assert as_int(None) == 0
    assert as_int(True) == 0
    assert as_int(-5) == 0
    assert as_int("12") == 0
    assert as_int(7.9) == 7
    assert as_int(42) == 42
