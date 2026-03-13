"""Rich tables for usage reports."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, tzinfo

from rich.panel import Panel
from rich.table import Table

from tokentally.aggregate import Totals
from tokentally.blocks import Block, is_active, projected_cost
from tokentally.charts import sparkline
from tokentally.fmt import human_tokens, money
from tokentally.pricing import Price
from tokentally.summary import Summary

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


def summary_panel(s: Summary) -> Panel:
    """Headline numbers plus a sparkline of daily cost."""
    grid = Table.grid(padding=(0, 2))
    grid.add_column(style="bold")
    grid.add_column()
    if s.first_day and s.last_day:
        grid.add_row("Period", f"{s.first_day} to {s.last_day} ({s.active_days} active days)")
    grid.add_row("Requests", f"{s.totals.requests:,}")
    grid.add_row("Tokens", human_tokens(s.totals.total_tokens))
    grid.add_row("Cost", money(s.totals.cost))
    grid.add_row("Per active day", money(s.cost_per_active_day))
    grid.add_row("Cache hit rate", f"{s.cache_hit_rate:.1%}")
    if s.top_model:
        grid.add_row("Top model", s.top_model)
    if s.top_project:
        grid.add_row("Top project", s.top_project)
    if s.daily_cost:
        grid.add_row("Daily cost", sparkline(s.daily_cost))
    return Panel(grid, title="tokentally", expand=False)


def blocks_table(blocks: list[Block], now: datetime, tz: tzinfo | None = None) -> Table:
    """One row per billing block; the running block shows a cost projection."""
    table = Table(header_style="bold")
    table.add_column("Start")
    table.add_column("Status")
    table.add_column("Requests", justify="right")
    table.add_column("Tokens", justify="right")
    table.add_column("Cost", justify="right")
    table.add_column("Projected", justify="right")
    for b in blocks:
        start = b.start.astimezone(tz).strftime("%Y-%m-%d %H:%M")
        if is_active(b, now):
            left = b.end - now
            status = f"active, {left.seconds // 3600}h{left.seconds % 3600 // 60:02d}m left"
            projected = money(projected_cost(b, now))
        else:
            status, projected = "done", ""
        table.add_row(
            start,
            status,
            f"{b.totals.requests:,}",
            human_tokens(b.totals.total_tokens),
            money(b.totals.cost),
            projected,
        )
    return table
