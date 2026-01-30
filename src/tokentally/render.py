"""Rich tables for usage reports."""

from __future__ import annotations

from rich.table import Table

from tokentally.aggregate import Totals
from tokentally.fmt import human_tokens, money

TOKEN_COLUMNS: list[tuple[str, str]] = [
    ("Input", "input_tokens"),
    ("Output", "output_tokens"),
    ("Cache write", "cache_creation_tokens"),
    ("Cache read", "cache_read_tokens"),
    ("Total", "total_tokens"),
]


def totals_table(groups: dict[str, Totals], key_title: str, grand: Totals) -> Table:
    """Build a table with one row per group and a grand total footer."""
    table = Table(show_footer=True, header_style="bold", footer_style="bold")
    table.add_column(key_title, footer="Total", overflow="fold")
    for title, attr in TOKEN_COLUMNS:
        table.add_column(title, justify="right", footer=human_tokens(getattr(grand, attr)))
    table.add_column("Cost", justify="right", footer=money(grand.cost))
    for key, t in groups.items():
        cells = [human_tokens(getattr(t, attr)) for _, attr in TOKEN_COLUMNS]
        table.add_row(key, *cells, money(t.cost))
    return table
