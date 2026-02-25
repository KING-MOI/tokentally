"""Standalone SVG charts."""

from __future__ import annotations

import math
from collections.abc import Callable
from dataclasses import dataclass
from xml.sax.saxutils import escape, quoteattr


@dataclass(frozen=True, slots=True)
class Theme:
    background: str
    text: str
    bar: str
    grid: str


THEMES: dict[str, Theme] = {
    "light": Theme(background="#ffffff", text="#1f2328", bar="#4f7cff", grid="#d0d7de"),
    "dark": Theme(background="#0d1117", text="#e6edf3", bar="#58a6ff", grid="#30363d"),
}


def bar_chart_svg(
    rows: list[tuple[str, float]],
    title: str = "",
    value_fmt: Callable[[float], str] = lambda v: f"{v:g}",
    width: int = 720,
    bar_height: int = 20,
    gap: int = 6,
    theme: Theme = THEMES["light"],
) -> str:
    """Render labelled values as a horizontal bar chart SVG document."""
    label_w = 8 * max((len(label) for label, _ in rows), default=0) + 16
    value_w = 8 * max((len(value_fmt(v)) for _, v in rows), default=0) + 16
    top_pad = 40 if title else 12
    plot_w = max(width - label_w - value_w, 10)
    height = top_pad + len(rows) * (bar_height + gap) + 12
    top = max((v for _, v in rows), default=0)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, monospace" font-size="13" '
        f'role="img" aria-label={quoteattr(title or "bar chart")}>',
        f'<rect width="{width}" height="{height}" fill="{theme.background}"/>',
        f'<g fill="{theme.text}">',
    ]
    if title:
        parts.append(
            f'<text x="12" y="24" font-size="16" font-weight="bold">{escape(title)}</text>'
        )
    for i, (label, value) in enumerate(rows):
        y = top_pad + i * (bar_height + gap)
        w = 0 if top <= 0 else value / top * plot_w
        mid = y + bar_height / 2 + 4
        parts.append(
            f'<text x="{label_w - 8}" y="{mid:.1f}" text-anchor="end">{escape(label)}</text>'
        )
        tip = escape(f"{label}: {value_fmt(value)}")
        parts.append(
            f'<rect x="{label_w}" y="{y}" width="{w:.1f}" height="{bar_height}" '
            f'fill="{theme.bar}" rx="2"><title>{tip}</title></rect>'
        )
        parts.append(
            f'<text x="{label_w + w + 6:.1f}" y="{mid:.1f}">{escape(value_fmt(value))}</text>'
        )
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def column_chart_svg(
    rows: list[tuple[str, float]],
    title: str = "",
    value_fmt: Callable[[float], str] = lambda v: f"{v:g}",
    height: int = 320,
    col_width: int = 24,
    gap: int = 8,
    theme: Theme = THEMES["light"],
) -> str:
    """Render a time series as vertical columns with a labelled value axis."""
    left, right, bottom = 80, 20, 80
    top_pad = 40 if title else 16
    width = max(left + len(rows) * (col_width + gap) + right, 320)
    plot_h = height - top_pad - bottom
    top = nice_ceiling(max((v for _, v in rows), default=0))
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="ui-monospace, monospace" font-size="12" '
        f'role="img" aria-label={quoteattr(title or "column chart")}>',
        f'<rect width="{width}" height="{height}" fill="{theme.background}"/>',
        f'<g fill="{theme.text}">',
    ]
    if title:
        parts.append(
            f'<text x="12" y="24" font-size="16" font-weight="bold">{escape(title)}</text>'
        )
    for step in range(5):
        frac = step / 4
        y = top_pad + plot_h - frac * plot_h
        parts.append(
            f'<line x1="{left}" y1="{y:.1f}" x2="{width - right}" y2="{y:.1f}" '
            f'stroke="{theme.grid}" stroke-width="1"/>'
        )
        parts.append(
            f'<text x="{left - 6}" y="{y + 4:.1f}" text-anchor="end">'
            f"{escape(value_fmt(top * frac))}</text>"
        )
    for i, (label, value) in enumerate(rows):
        x = left + gap / 2 + i * (col_width + gap)
        h = 0 if top <= 0 else value / top * plot_h
        y = top_pad + plot_h - h
        tip = escape(f"{label}: {value_fmt(value)}")
        parts.append(
            f'<rect x="{x:.1f}" y="{y:.1f}" width="{col_width}" height="{h:.1f}" '
            f'fill="{theme.bar}" rx="2"><title>{tip}</title></rect>'
        )
        lx = x + col_width / 2
        ly = top_pad + plot_h + 12
        parts.append(
            f'<text x="{lx:.1f}" y="{ly:.1f}" text-anchor="end" '
            f'transform="rotate(-45 {lx:.1f} {ly:.1f})">{escape(label)}</text>'
        )
    parts.append("</g>")
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def nice_ceiling(value: float) -> float:
    """Round ``value`` up to 1, 2, 2.5 or 5 times a power of ten."""
    if value <= 0:
        return 0.0
    exponent = math.floor(math.log10(value))
    base = 10.0**exponent
    for step in (1, 2, 2.5, 5, 10):
        if value <= step * base + 1e-9 * base:
            return step * base
    return 10 * base
