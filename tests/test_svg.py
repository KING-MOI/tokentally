import xml.etree.ElementTree as ET

from tokentally.svg import bar_chart_svg

NS = "{http://www.w3.org/2000/svg}"


def test_svg_is_well_formed_with_one_bar_per_row() -> None:
    doc = bar_chart_svg([("a", 1), ("b", 2)], title="Usage")
    root = ET.fromstring(doc)
    bars = [r for r in root.iter(f"{NS}rect") if r.get("fill") == "#4f7cff"]
    assert len(bars) == 2
    assert float(bars[1].get("width", 0)) > float(bars[0].get("width", 0))


def test_labels_are_escaped() -> None:
    doc = bar_chart_svg([("<script>&", 1)])
    ET.fromstring(doc)
    assert "<script>" not in doc


def test_empty_chart_is_still_valid_svg() -> None:
    ET.fromstring(bar_chart_svg([]))


def test_bars_carry_hover_titles() -> None:
    root = ET.fromstring(bar_chart_svg([("opus", 12.5)], value_fmt=lambda v: f"${v:.2f}"))
    titles = [t.text for t in root.iter(f"{NS}title")]
    assert "opus: $12.50" in titles


def test_svg_has_accessible_label() -> None:
    root = ET.fromstring(bar_chart_svg([("a", 1)], title='Cost "by" model'))
    assert root.get("role") == "img"
    assert root.get("aria-label") == 'Cost "by" model'


def test_dark_theme_changes_background() -> None:
    from tokentally.svg import THEMES

    doc = bar_chart_svg([("a", 1)], theme=THEMES["dark"])
    assert THEMES["dark"].background in doc
    assert THEMES["light"].background not in doc


def test_column_chart_bars_grow_upward_from_a_shared_baseline() -> None:
    from tokentally.svg import column_chart_svg

    root = ET.fromstring(column_chart_svg([("03-01", 1), ("03-02", 4)], title="Daily"))
    bars = [r for r in root.iter(f"{NS}rect") if r.find(f"{NS}title") is not None]
    assert len(bars) == 2
    bottoms = {round(float(b.get("y", 0)) + float(b.get("height", 0)), 1) for b in bars}
    assert len(bottoms) == 1
    assert float(bars[1].get("height", 0)) == 4 * float(bars[0].get("height", 0))


def test_column_chart_draws_five_gridlines() -> None:
    from tokentally.svg import column_chart_svg

    root = ET.fromstring(column_chart_svg([("a", 1)]))
    assert len(list(root.iter(f"{NS}line"))) == 5
