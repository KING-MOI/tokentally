import pytest

from conftest import make_record
from tokentally.aggregate import group


def test_group_by_day_sums_tokens_and_counts_requests() -> None:
    records = [
        make_record("2026-03-01T01:00:00", input_tokens=10, output_tokens=5),
        make_record("2026-03-01T23:00:00", input_tokens=1, output_tokens=1),
        make_record("2026-03-02T00:00:00", output_tokens=100),
    ]
    days = group(records, "day")
    assert list(days) == ["2026-03-01", "2026-03-02"]
    assert days["2026-03-01"].total_tokens == 17
    assert days["2026-03-01"].requests == 2


def test_group_by_model_prices_each_record() -> None:
    records = [make_record(model="claude-sonnet-4-5", output_tokens=1_000_000)]
    assert group(records, "model")["claude-sonnet-4-5"].cost == pytest.approx(15.0)


def test_records_without_project_are_grouped_together() -> None:
    projects = group([make_record(project=""), make_record(project="")], "project")
    assert list(projects) == ["(none)"]


def test_week_and_month_keys() -> None:
    records = [make_record("2026-01-01T10:00:00"), make_record("2026-12-31T10:00:00")]
    assert list(group(records, "month")) == ["2026-01", "2026-12"]
    assert list(group(records, "week")) == ["2026-W01", "2026-W53"]
