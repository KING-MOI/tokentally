from rich.console import Console

from tokentally.aggregate import group, total
from tokentally.render import totals_table

from conftest import make_record


def render(table: object) -> str:
    console = Console(width=120, record=True, color_system=None)
    console.print(table)
    return console.export_text()


def test_table_has_a_row_per_group_and_a_total_footer() -> None:
    records = [
        make_record(model="claude-sonnet-4-5", output_tokens=2_000_000),
        make_record(model="claude-haiku-4-5", input_tokens=1_500),
    ]
    text = render(totals_table(group(records, "model"), "Model", total(records)))
    assert "claude-sonnet-4-5" in text
    assert "claude-haiku-4-5" in text
    assert "2.0M" in text
    assert "$30.00" in text
    assert "Total" in text


def test_metric_rows() -> None:
    import pytest

    from tokentally.render import metric_rows

    groups = group([make_record(output_tokens=1_000_000)], "model")
    assert metric_rows(groups, "tokens") == [("claude-sonnet-4-5", 1_000_000.0)]
    assert metric_rows(groups, "cost")[0][1] == pytest.approx(15.0)
    with pytest.raises(ValueError):
        metric_rows(groups, "vibes")


def test_prices_table_marks_overrides() -> None:
    from tokentally.pricing import Price
    from tokentally.render import prices_table

    text = render(prices_table({"a": Price(1, 2), "b": Price(0.5, 4, 0.6, 0.05)}, {"b"}))
    assert "b *" in text
    assert "0.05" in text
    assert "a *" not in text


def test_summary_panel_shows_headline_numbers() -> None:
    from datetime import UTC

    from tokentally.render import summary_panel
    from tokentally.summary import summarize

    records = [
        make_record("2026-03-01T10:00:00", output_tokens=1_000_000),
        make_record("2026-03-04T10:00:00", output_tokens=500_000),
    ]
    text = render(summary_panel(summarize(records, tz=UTC)))
    assert "2026-03-01 to 2026-03-04 (2 active days)" in text
    assert "$22.50" in text
    assert "claude-sonnet-4-5" in text
    assert "█" in text


def test_blocks_table_marks_the_running_block() -> None:
    from datetime import UTC, datetime

    from tokentally.blocks import billing_blocks
    from tokentally.render import blocks_table

    blocks = billing_blocks(
        [make_record("2026-03-01T01:00:00"), make_record("2026-03-01T10:15:00", output_tokens=9)]
    )
    now = datetime(2026, 3, 1, 11, 30, tzinfo=UTC)
    text = render(blocks_table(blocks, now, UTC))
    assert "2026-03-01 01:00" in text
    assert "done" in text
    assert "active, 3h30m left" in text
