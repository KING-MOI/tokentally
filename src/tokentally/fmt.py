"""Number formatting for terminal output."""

from __future__ import annotations


def human_tokens(n: int) -> str:
    """Format a token count compactly: 950, 1.2k, 3.4M, 1.1B."""
    for size, suffix in ((1_000_000_000, "B"), (1_000_000, "M"), (1_000, "k")):
        if round(n / size, 1) >= 1:
            return f"{n / size:.1f}{suffix}"
    return str(n)


def money(amount: float) -> str:
    return f"${amount:,.2f}"
