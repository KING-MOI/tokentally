"""Plain-text charts for the terminal."""

from __future__ import annotations

BLOCKS = " ▏▎▍▌▋▊▉█"


def bar(value: float, max_value: float, width: int) -> str:
    """Render ``value`` as a horizontal bar with 1/8 character resolution."""
    if max_value <= 0 or value <= 0:
        return ""
    eighths = round(value / max_value * width * 8)
    full, rest = divmod(eighths, 8)
    return "█" * full + (BLOCKS[rest] if rest else "")
