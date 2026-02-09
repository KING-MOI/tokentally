from datetime import date, timezone, UTC

import pytest

from conftest import make_record
from tokentally.filters import filter_records, parse_date

TODAY = date(2026, 3, 10)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("2026-03-01", date(2026, 3, 1)),
        ("20260301", date(2026, 3, 1)),
        ("today", TODAY),
        ("Yesterday", date(2026, 3, 9)),
        ("7d", date(2026, 3, 3)),
        ("2w", date(2026, 2, 24)),
    ],
)
def test_parse_date(text: str, expected: date) -> None:
    assert parse_date(text, TODAY) == expected


def test_parse_date_rejects_garbage() -> None:
    with pytest.raises(ValueError):
        parse_date("last tuesday", TODAY)


def test_since_and_until_are_inclusive() -> None:
    records = [make_record(f"2026-03-0{d}T12:00:00") for d in range(1, 6)]
    kept = filter_records(records, date(2026, 3, 2), date(2026, 3, 4), tz=UTC)
    assert [r.timestamp.day for r in kept] == [2, 3, 4]


def test_model_project_and_source_filters() -> None:
    records = [
        make_record(model="claude-opus-4-1", project="Acme"),
        make_record(model="claude-sonnet-4-5", project="acme"),
        make_record(model="gpt-5", project="widgets", source="codex"),
    ]
    assert len(filter_records(records, model="OPUS")) == 1
    assert len(filter_records(records, project="acme")) == 2
    assert len(filter_records(records, sources=["codex"])) == 1
