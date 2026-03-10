from datetime import UTC, date

import pytest

from conftest import make_record
from tokentally.summary import summarize


def test_summary_of_two_active_days_over_three() -> None:
    records = [
        make_record("2026-03-01T10:00:00", model="claude-opus-4-1", output_tokens=1_000_000),
        make_record("2026-03-03T10:00:00", model="claude-haiku-4-5", input_tokens=1_000_000),
    ]
    s = summarize(records, tz=UTC)
    assert (s.first_day, s.last_day) == (date(2026, 3, 1), date(2026, 3, 3))
    assert s.active_days == 2
    assert s.daily_cost == pytest.approx([75.0, 0.0, 1.0])
    assert s.cost_per_active_day == pytest.approx(38.0)
    assert s.top_model == "claude-opus-4-1"


def test_cache_hit_rate() -> None:
    s = summarize([make_record(input_tokens=10, cache_creation_tokens=10, cache_read_tokens=80)])
    assert s.cache_hit_rate == pytest.approx(0.8)


def test_empty_summary() -> None:
    s = summarize([])
    assert s.first_day is None
    assert s.daily_cost == []
    assert s.cost_per_active_day == 0.0
    assert s.cache_hit_rate == 0.0
    assert s.top_model is None
