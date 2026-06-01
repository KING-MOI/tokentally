import os
from datetime import UTC
from pathlib import Path

import pytest

from tokentally.aggregate import group

from conftest import make_record


def test_group_by_day_sums_tokens_and_counts_requests() -> None:
    records = [
        make_record("2026-03-01T01:00:00", input_tokens=10, output_tokens=5),
        make_record("2026-03-01T23:00:00", input_tokens=1, output_tokens=1),
        make_record("2026-03-02T00:00:00", output_tokens=100),
    ]
    days = group(records, "day", tz=UTC)
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
    assert list(group(records, "month", tz=UTC)) == ["2026-01", "2026-12"]
    assert list(group(records, "week", tz=UTC)) == ["2026-W01", "2026-W53"]


def test_days_are_bucketed_in_the_requested_timezone() -> None:
    from zoneinfo import ZoneInfo

    late_evening_la = make_record("2026-03-02T03:00:00", output_tokens=1)
    days = group([late_evening_la], "day", tz=ZoneInfo("America/Los_Angeles"))
    assert list(days) == ["2026-03-01"]


def test_total_of_nothing_is_zero() -> None:
    from tokentally.aggregate import total

    t = total([])
    assert (t.total_tokens, t.cost, t.requests) == (0, 0.0, 0)


def test_totals_track_first_and_last_seen() -> None:
    from tokentally.aggregate import total

    t = total([make_record("2026-03-02T00:00:00"), make_record("2026-03-01T00:00:00")])
    assert t.first_seen is not None and t.last_seen is not None
    assert t.first_seen.day == 1 and t.last_seen.day == 2


def test_sort_groups_by_cost_descending() -> None:
    from tokentally.aggregate import sort_groups

    groups = group(
        [
            make_record(model="claude-haiku-4-5", output_tokens=1000),
            make_record(model="claude-opus-4-1", output_tokens=1000),
        ],
        "model",
    )
    assert list(sort_groups(groups, "cost")) == ["claude-opus-4-1", "claude-haiku-4-5"]
    with pytest.raises(ValueError):
        sort_groups(groups, "vibes")


def test_dated_snapshots_share_a_row_with_the_base_model() -> None:
    from tokentally.aggregate import base_model

    records = [
        make_record(model="claude-haiku-4-5-20251001"),
        make_record(model="claude-haiku-4-5"),
        make_record(model="claude-sonnet-4-5@20250929"),
    ]
    assert list(group(records, "model")) == ["claude-haiku-4-5", "claude-sonnet-4-5"]
    assert base_model("gpt-5-2025-08-07") == "gpt-5"
    assert base_model("gemini-2.5-flash") == "gemini-2.5-flash"


def test_daily_series_fills_missing_days() -> None:
    from datetime import date

    from tokentally.aggregate import daily_series

    days = group(
        [make_record("2026-03-01T10:00:00"), make_record("2026-03-03T10:00:00")],
        "day",
        tz=UTC,
    )
    series = daily_series(days, date(2026, 3, 1), date(2026, 3, 3))
    assert [k for k, _ in series] == ["2026-03-01", "2026-03-02", "2026-03-03"]
    assert series[1][1].requests == 0


def test_breakdown_splits_each_day_by_model() -> None:
    from tokentally.aggregate import breakdown

    records = [
        make_record("2026-03-01T10:00:00", model="claude-opus-4-1"),
        make_record("2026-03-01T11:00:00", model="claude-haiku-4-5"),
        make_record("2026-03-02T10:00:00", model="claude-haiku-4-5"),
    ]
    nested = breakdown(records, "day", "model", tz=UTC)
    assert {k: list(v) for k, v in nested.items()} == {
        "2026-03-01": ["claude-haiku-4-5", "claude-opus-4-1"],
        "2026-03-02": ["claude-haiku-4-5"],
    }


def test_weekday_and_hour_of_day_keys_sort_naturally() -> None:
    records = [
        make_record("2026-03-01T23:30:00"),
        make_record("2026-03-02T09:00:00"),
        make_record("2026-03-09T09:15:00"),
    ]
    assert list(group(records, "weekday", tz=UTC)) == ["1 Mon", "7 Sun"]
    hours = group(records, "hour_of_day", tz=UTC)
    assert list(hours) == ["09:00", "23:00"]
    assert hours["09:00"].requests == 2


def test_projects_under_home_are_shown_with_tilde(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    from conftest import set_home

    set_home(monkeypatch, tmp_path)
    records = [
        make_record(project=str(tmp_path / "work" / "app")),
        make_record(project="/srv/app"),
    ]
    assert list(group(records, "project")) == ["/srv/app", f"~{os.sep}work{os.sep}app"]
