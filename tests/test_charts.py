from tokentally.charts import bar


def test_full_bar_fills_width() -> None:
    assert bar(10, 10, 5) == "█████"


def test_partial_cells_use_eighth_blocks() -> None:
    assert bar(1, 16, 1) == "▏"
    assert bar(1, 8, 1) == "▏"
    assert bar(5, 10, 1) == "▌"


def test_zero_and_empty_scale_render_nothing() -> None:
    assert bar(0, 10, 5) == ""
    assert bar(3, 0, 5) == ""


def test_tiny_nonzero_value_is_still_visible() -> None:
    assert bar(1, 1_000_000, 10) == "▏"


def test_bar_chart_aligns_labels_and_values() -> None:
    from tokentally.charts import bar_chart

    lines = bar_chart([("mon", 2), ("tuesday", 4)], width=4)
    assert lines == ["mon     │██   2", "tuesday │████ 4"]


def test_bar_chart_of_nothing_is_empty() -> None:
    from tokentally.charts import bar_chart

    assert bar_chart([]) == []


def test_sparkline_spans_low_to_high() -> None:
    from tokentally.charts import sparkline

    assert sparkline([0, 7, 14]) == "▁▅█"
    assert sparkline([3, 3]) == "▁▁"
    assert sparkline([]) == ""
