"""Rich tables for usage reports."""

from __future__ import annotations

from collections.abc import Callable

from rich.table import Table

from tokentally.aggregate import Totals
from tokentally.fmt import human_tokens, money
from tokentally.pricing import Price

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


def metric_rows(groups: dict[str, Totals], metric: str) -> list[tuple[str, float]]:
    """Pick the charted value for each group: ``cost`` or ``tokens``."""
    if metric == "cost":
        return [(k, t.cost) for k, t in groups.items()]
    if metric == "tokens":
        return [(k, float(t.total_tokens)) for k, t in groups.items()]
    raise ValueError(f"unknown metric: {metric}")


def metric_format(metric: str) -> Callable[[float], str]:
    """Return the formatter matching a metric's unit."""
    if metric == "cost":
        return money
    return lambda v: human_tokens(int(v))


def prices_table(prices: dict[str, Price], overridden: set[str] | None = None) -> Table:
    """List per-million-token prices; config overrides are starred."""
    overridden = overridden or set()
    table = Table(header_style="bold", caption="USD per million tokens, * = from config")
    table.add_column("Model")
    for title in ("Input", "Output", "Cache write", "Cache read"):
        table.add_column(title, justify="right")
    for model in sorted(prices):
        p = prices[model]
        name = f"{model} *" if model in overridden else model
        table.add_row(name, *(f"{v:g}" for v in (p.input, p.output, p.cache_write, p.cache_read)))
    return table
