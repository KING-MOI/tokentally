"""Implementations of the tokentally subcommands."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, datetime, timedelta, tzinfo
from pathlib import Path

from rich.console import Console, RenderableType
from rich.live import Live
from rich.table import Table

from tokentally.aggregate import Totals, breakdown, group, sort_groups, total
from tokentally.blocks import billing_blocks, is_active
from tokentally.cache import FileCache, cache_path
from tokentally.config import Config, config_path, write_template
from tokentally.discovery import describe_roots, load_records
from tokentally.export import records_jsonl, summary_json, to_csv, to_json
from tokentally.filters import filter_records
from tokentally.fmt import human_tokens, money
from tokentally.models import UsageRecord
from tokentally.parsers import PARSERS
from tokentally.pricing import PRICES, unpriced_models
from tokentally.render import (
    blocks_table,
    chart_text,
    metric_format,
    metric_rows,
    prices_table,
    summary_panel,
    totals_table,
)
from tokentally.summary import summarize
from tokentally.svg import THEMES, bar_chart_svg, column_chart_svg


class CliError(Exception):
    """An expected failure, reported as one line on stderr without a traceback."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


TIME_KEYS = {"hour", "day", "week", "month"}


def config_command(action: str) -> int:
    path = config_path()
    if action == "path":
        print(path)
    elif action == "init":
        try:
            write_template(path)
        except FileExistsError:
            print(f"tokentally: {path} already exists", file=sys.stderr)
            return 1
        print(f"wrote {path}")
    elif path.exists():
        print(path.read_text(encoding="utf-8"), end="")
    else:
        print(f"tokentally: no config at {path}", file=sys.stderr)
        return 1
    return 0


def pricing_command(query: str | None, config: Config) -> int:
    prices = {**PRICES, **config.prices}
    if query:
        prices = {k: v for k, v in prices.items() if query.lower() in k}
    Console().print(prices_table(prices, set(config.prices)))
    return 0


def summary_command(args: argparse.Namespace, config: Config) -> int:
    s = summarize(select_records(args, config), {**PRICES, **config.prices}, tz=args.tz)
    if args.format == "json":
        print(summary_json(s))
    else:
        Console().print(summary_panel(s, config.budget))
    return 0


def blocks_view(args: argparse.Namespace, config: Config) -> RenderableType:
    now = datetime.now(UTC)
    blocks = billing_blocks(
        select_records(args, config),
        {**PRICES, **config.prices},
        timedelta(hours=args.hours),
    )
    if args.active:
        blocks = [b for b in blocks if is_active(b, now)]
        if not blocks:
            return "no active block"
    return blocks_table(blocks, now, args.tz)


def blocks_command(args: argparse.Namespace, config: Config) -> int:
    console = Console()
    if not args.watch:
        console.print(blocks_view(args, config))
        return 0
    with Live(console=console, auto_refresh=False) as live:
        while True:
            live.update(blocks_view(args, config), refresh=True)
            time.sleep(args.watch)


def paths_command(config: Config) -> int:
    table = Table(header_style="bold")
    table.add_column("Source")
    table.add_column("Directory")
    table.add_column("Log files", justify="right")
    for source, root, count in describe_roots(PARSERS, config.paths):
        table.add_row(source, str(root), "missing" if count is None else str(count))
    table.add_row("cache", str(cache_path()), "", style="dim")
    Console().print(table)
    return 0


def chart_subtitle(grand: Totals, tz: tzinfo | None) -> str:
    """Date span and totals, e.g. ``2026-03-01 to 2026-03-03 · 30.3k tokens · $0.12``."""
    if grand.first_seen is None or grand.last_seen is None:
        return ""
    first = grand.first_seen.astimezone(tz).date()
    last = grand.last_seen.astimezone(tz).date()
    return f"{first} to {last} · {human_tokens(grand.total_tokens)} tokens · {money(grand.cost)}"


def emit(text: str, path: Path | None) -> None:
    """Write machine-readable output to ``path``, or stdout when not given."""
    if path is None:
        sys.stdout.write(text)
        return
    try:
        path.write_text(text, encoding="utf-8")
    except OSError as exc:
        raise CliError(f"cannot write {path}: {exc.strerror}", code=1) from exc


def select_records(args: argparse.Namespace, config: Config) -> list[UsageRecord]:
    """Load records and apply the selection options shared by every report."""
    if args.since and args.until and args.since > args.until:
        raise CliError(f"--since {args.since} is after --until {args.until}")
    cache = None if args.no_cache else FileCache(cache_path())
    records = load_records(args.source or PARSERS, config.paths, cache)
    if cache:
        try:
            cache.save()
        except OSError as exc:
            print(f"tokentally: could not save cache: {exc}", file=sys.stderr)
    return filter_records(
        records,
        since=args.since,
        until=args.until,
        model=args.model,
        project=args.project,
        session=args.session,
        tz=args.tz,
    )


def run_report(args: argparse.Namespace, config: Config) -> int:
    key, title = args.report
    tz = args.tz
    records = select_records(args, config)
    prices = {**PRICES, **config.prices}
    missing = unpriced_models((r.model for r in records), prices)
    if missing:
        print(
            "tokentally: no price for " + ", ".join(missing) + " (counted as $0)",
            file=sys.stderr,
        )
    grand = total(records, prices)
    groups = sort_groups(group(records, key, prices, tz=tz), args.sort)
    if args.limit is not None:
        groups = dict(list(groups.items())[: args.limit])
    rows = metric_rows(groups, args.metric)
    value_fmt = metric_format(args.metric)
    if args.output and args.format == "table":
        raise CliError("--output needs --format json or csv")
    if args.svg:
        render_svg = column_chart_svg if key in TIME_KEYS else bar_chart_svg
        doc = render_svg(
            rows,
            f"{title} by {args.metric}",
            value_fmt,
            theme=THEMES[args.svg_theme],
            subtitle=chart_subtitle(grand, tz),
        )
        try:
            args.svg.write_text(doc, encoding="utf-8")
        except OSError as exc:
            raise CliError(f"cannot write {args.svg}: {exc.strerror}", code=1) from exc
    nested = None
    if args.breakdown:
        nested = {
            k: sort_groups(v, args.sort)
            for k, v in breakdown(records, key, args.breakdown, prices, tz=tz).items()
        }
    if args.format == "json":
        emit(to_json(groups, key, grand, nested, args.breakdown or "") + "\n", args.output)
        return 0
    if args.format == "csv":
        emit(to_csv(groups, key, nested, args.breakdown or ""), args.output)
        return 0
    console = Console()
    if not records:
        console.print("no usage found for the selected logs and filters", style="yellow")
        return 0
    console.print(
        totals_table(groups, title, grand, nested, compact=args.compact, share=args.share)
    )
    if args.chart:
        label_w = max((len(k) for k, _ in rows), default=0)
        value_w = max((len(value_fmt(v)) for _, v in rows), default=0)
        width = max(console.width - label_w - value_w - 4, 10)
        console.print(chart_text(rows, width, value_fmt), highlight=False, end="")
    return 0


def records_command(args: argparse.Namespace, config: Config) -> int:
    prices = {**PRICES, **config.prices}
    for line in records_jsonl(select_records(args, config), prices):
        print(line)
    return 0
