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
