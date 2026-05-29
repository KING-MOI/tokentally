"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
import time
from datetime import UTC, date, datetime, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.console import Console, RenderableType
from rich.live import Live
from rich.table import Table

from tokentally import __version__
from tokentally.aggregate import Totals, breakdown, group, sort_groups, total
from tokentally.blocks import billing_blocks, is_active
from tokentally.cache import FileCache, cache_path
from tokentally.config import (
    Config,
    ConfigError,
    config_path,
    load_config,
    write_template,
)
from tokentally.discovery import describe_roots, load_records
from tokentally.export import records_jsonl, summary_json, to_csv, to_json
from tokentally.filters import filter_records, parse_date
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

REPORTS: dict[str, tuple[str, str]] = {
    "hourly": ("hour", "Hour"),
    "daily": ("day", "Date"),
    "weekly": ("week", "Week"),
    "monthly": ("month", "Month"),
    "models": ("model", "Model"),
    "sessions": ("session", "Session"),
    "projects": ("project", "Project"),
    "sources": ("source", "Source"),
    "weekdays": ("weekday", "Weekday"),
    "hours": ("hour_of_day", "Hour"),
}


class CliError(Exception):
    """An expected failure, reported as one line on stderr without a traceback."""

    def __init__(self, message: str, code: int = 2) -> None:
        super().__init__(message)
        self.code = code


TIME_KEYS = {"hour", "day", "week", "month"}
COMMANDS = {*REPORTS, "blocks", "config", "paths", "pricing", "records", "summary"}


def _date(value: str) -> date:
    try:
        return parse_date(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            f"invalid date {value!r} (use YYYY-MM-DD, today, yesterday or Nd)"
        ) from exc


def _positive(value: str) -> int:
    try:
        n = int(value)
    except ValueError:
        n = 0
    if n < 1:
        raise argparse.ArgumentTypeError(f"expected a positive integer, got {value!r}")
    return n


def _zone(name: str) -> tzinfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"unknown timezone: {name}") from exc


def build_parser(config: Config | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tokentally")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    selection = argparse.ArgumentParser(add_help=False)
    selection.add_argument("--since", type=_date, help="first day to include")
    selection.add_argument("--until", type=_date, help="last day to include")
    selection.add_argument(
        "--source",
        action="append",
        choices=sorted(PARSERS),
        help="only read logs from this agent (repeatable)",
    )
    selection.add_argument(
        "--no-cache",
        action="store_true",
        help="re-read every log instead of using the parse cache",
    )
    selection.add_argument("--model", help="only models whose name contains this")
    selection.add_argument("--project", help="only projects whose name contains this")
    selection.add_argument("--session", help="only sessions whose id starts with this")
    selection.add_argument(
        "--tz",
        type=_zone,
        help="IANA timezone for day boundaries (default: local time)",
    )
    common = argparse.ArgumentParser(add_help=False, parents=[selection])
    common.add_argument(
        "--sort",
        choices=["key", "cost", "tokens"],
        default="key",
        help="row order (cost and tokens sort descending)",
    )
    common.add_argument("--limit", type=_positive, metavar="N", help="show only the first N rows")
    common.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="output format",
    )
    common.add_argument(
        "--breakdown",
        choices=["model", "project", "source"],
        help="split each row by this field",
    )
    common.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="write json or csv output to FILE instead of stdout",
    )
    common.add_argument("--compact", action="store_true", help="hide cache token columns")
    common.add_argument("--chart", action="store_true", help="draw a bar chart under the table")
    common.add_argument(
        "--metric",
        choices=["cost", "tokens"],
        default="cost",
        help="value to chart",
    )
    common.add_argument("--svg", type=Path, metavar="FILE", help="also write the chart as SVG")
    common.add_argument(
        "--svg-theme",
        choices=sorted(THEMES),
        default="light",
        help="color theme for --svg",
    )
    sub = parser.add_subparsers(dest="command")
    sub.add_parser("records", parents=[selection], help="dump matching records as json lines")
    sub.add_parser("paths", help="show where logs are searched for")
    pricing = sub.add_parser("pricing", help="list known model prices")
    pricing.add_argument("model", nargs="?", help="only models whose name contains this")
    cfg = sub.add_parser("config", help="show or create the config file")
    cfg.add_argument("action", choices=["path", "init", "show"], nargs="?", default="path")
    summary = sub.add_parser("summary", parents=[selection], help="headline numbers")
    summary.add_argument("--format", choices=["table", "json"], default="table")
    blocks = sub.add_parser("blocks", parents=[selection], help="five hour billing windows")
    blocks.add_argument("--active", action="store_true", help="only the running block")
    blocks.add_argument(
        "--watch",
        type=float,
        nargs="?",
        const=10.0,
        metavar="SECONDS",
        help="redraw every SECONDS (default 10) until ctrl-c",
    )
    reports = [sub.add_parser(name, parents=[common]) for name in REPORTS]
    if config:
        _apply_defaults([summary, blocks, *reports], config.defaults)
    return parser


def _apply_defaults(parsers: list[argparse.ArgumentParser], defaults: dict[str, Any]) -> None:
    """Use config values as option defaults, validated like command line input.

    A key only has to be known to one of the parsers; each parser picks up the
    keys it has an option for.
    """
    actions = {a.dest: a for p in parsers for a in p._actions}
    for name, value in defaults.items():
        action = actions.get(name)
        if action is None or name in ("help", "since", "until", "svg"):
            raise ConfigError(f"unknown option in [defaults]: {name}")
        values = value if isinstance(value, list) else [value]
        if action.choices is not None and any(v not in action.choices for v in values):
            raise ConfigError(f"invalid value for {name} in [defaults]: {value!r}")
    for parser in parsers:
        known = {a.dest for a in parser._actions}
        parser.set_defaults(**{k: v for k, v in defaults.items() if k in known})


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
    blocks = billing_blocks(select_records(args, config), {**PRICES, **config.prices})
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


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv or argv[0] not in COMMANDS and argv[0] not in ("-h", "--help", "--version"):
        argv.insert(0, "daily")
    if argv[0] == "config":
        return config_command(build_parser().parse_args(argv).action)
    try:
        config = load_config()
        parser = build_parser(config)
    except ConfigError as exc:
        print(f"tokentally: config error: {exc}", file=sys.stderr)
        return 2
    args = parser.parse_args(argv)
    try:
        return dispatch(args, config)
    except CliError as exc:
        print(f"tokentally: {exc}", file=sys.stderr)
        return exc.code


def dispatch(args: argparse.Namespace, config: Config) -> int:
    if args.command == "paths":
        return paths_command(config)
    if args.command == "pricing":
        return pricing_command(args.model, config)
    if args.command == "summary":
        return summary_command(args, config)
    if args.command == "blocks":
        return blocks_command(args, config)
    if args.command == "records":
        prices = {**PRICES, **config.prices}
        for line in records_jsonl(select_records(args, config), prices):
            print(line)
        return 0
    return run_report(args, config)


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
    key, title = REPORTS[args.command]
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
    console.print(totals_table(groups, title, grand, nested, compact=args.compact))
    if args.chart:
        label_w = max((len(k) for k, _ in rows), default=0)
        value_w = max((len(value_fmt(v)) for _, v in rows), default=0)
        width = max(console.width - label_w - value_w - 4, 10)
        console.print(chart_text(rows, width, value_fmt), highlight=False, end="")
    return 0
