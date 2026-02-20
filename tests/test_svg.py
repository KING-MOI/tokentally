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
