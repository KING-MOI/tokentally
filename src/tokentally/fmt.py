"""Number formatting for terminal output."""

from __future__ import annotations


def human_tokens(n: int) -> str:
    """Format a token count compactly: 950, 1.2k, 3.4M, 1.1B."""
    if n < 1_000:
        return str(n)
    for size, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if round(n / size, 1) >= 1:
            return f"{n / size:.1f}{suffix}"
    return str(n)


def money(amount: float) -> str:
    if 0 < amount < 0.005:
        return "<$0.01"
    return f"${amount:,.2f}"


def percent(part: float, whole: float) -> str:
    if whole <= 0:
        return "-"
    return f"{part / whole * 100:.1f}%"
