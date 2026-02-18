"""Standalone SVG charts."""

from __future__ import annotations

from collections.abc import Callable
from xml.sax.saxutils import escape


def bar_chart_svg(
    rows: list[tuple[str, float]],
    title: str = "",
    value_fmt: Callable[[float], str] = lambda v: f"{v:g}",
    width: int = 720,
    bar_height: int = 20,
    gap: int = 6,
    color: str = "#4f7cff",
) -> str:
    """Render labelled values as a horizontal bar chart SVG document."""
    label_w = 8 * max((len(label) for label, _ in rows), default=0) + 16
    value_w = 90
    top_pad = 40 if title else 12
    plot_w = max(width - label_w - value_w, 10)
    height = top_pad + len(rows) * (bar_height + gap) + 12
    top = max((v for _, v in rows), default=0)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, monospace" font-size="13">',
        f'<rect width="{width}" height="{height}" fill="#ffffff"/>',
    ]
    if title:
        parts.append(f'<text x="12" y="24" font-size="16" font-weight="bold">{escape(title)}</text>')
    for i, (label, value) in enumerate(rows):
        y = top_pad + i * (bar_height + gap)
        w = 0 if top <= 0 else value / top * plot_w
        mid = y + bar_height / 2 + 4
        parts.append(f'<text x="{label_w - 8}" y="{mid:.1f}" text-anchor="end">{escape(label)}</text>')
        parts.append(
            f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_height}" fill="{color}" rx="2"/>'
        )
        parts.append(f'<text x="{label_w + w + 6:.1f}" y="{mid:.1f}">{escape(value_fmt(value))}</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
