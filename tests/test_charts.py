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
