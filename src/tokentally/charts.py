"""Plain-text charts for the terminal."""

from __future__ import annotations

from collections.abc import Callable

BLOCKS = " ▏▎▍▌▋▊▉█"


def bar(value: float, max_value: float, width: int) -> str:
    """Render ``value`` as a horizontal bar with 1/8 character resolution."""
    if max_value <= 0 or value <= 0:
        return ""
    eighths = max(round(value / max_value * width * 8), 1)
    full, rest = divmod(eighths, 8)
    return "█" * full + (BLOCKS[rest] if rest else "")


def bar_chart(
    rows: list[tuple[str, float]],
    width: int = 40,
    value_fmt: Callable[[float], str] = lambda v: f"{v:g}",
) -> list[str]:
    """Render labelled rows as aligned bars, one line per row."""
    if not rows:
        return []
    label_w = max(len(label) for label, _ in rows)
    top = max(value for _, value in rows)
    lines = []
    for label, value in rows:
        drawn = bar(value, top, width)
        lines.append(f"{label.ljust(label_w)} │{drawn.ljust(width)} {value_fmt(value)}")
    return lines


SPARKS = "▁▂▃▄▅▆▇█"


def sparkline(values: list[float]) -> str:
    """Compress a series into one line of block characters."""
    if not values:
        return ""
    lo, hi = min(values), max(values)
    if hi == lo:
        return SPARKS[0] * len(values)
    span = hi - lo
    return "".join(SPARKS[round((v - lo) / span * (len(SPARKS) - 1))] for v in values)
