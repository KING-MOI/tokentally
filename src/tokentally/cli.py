"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from datetime import tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.console import Console

from tokentally import __version__
from tokentally.aggregate import group, sort_groups, total
from tokentally.charts import bar_chart
from tokentally.config import (
    Config,
    ConfigError,
    config_path,
    load_config,
    write_template,
)
from tokentally.discovery import load_records
from tokentally.export import to_csv, to_json
from tokentally.filters import filter_records, parse_date
from tokentally.parsers import PARSERS
from tokentally.pricing import PRICES
from tokentally.render import metric_format, metric_rows, totals_table
from tokentally.svg import THEMES, bar_chart_svg, column_chart_svg

REPORTS: dict[str, tuple[str, str]] = {
    "daily": ("day", "Date"),
    "weekly": ("week", "Week"),
    "monthly": ("month", "Month"),
    "models": ("model", "Model"),
    "sessions": ("session", "Session"),
    "projects": ("project", "Project"),
    "sources": ("source", "Source"),
}

TIME_KEYS = {"day", "week", "month"}
COMMANDS = {*REPORTS, "config"}


def _zone(name: str) -> tzinfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"unknown timezone: {name}") from exc


def build_parser(config: Config | None = None) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="tokentally")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--since", type=parse_date, help="first day to include")
    common.add_argument("--until", type=parse_date, help="last day to include")
    common.add_argument(
        "--source",
        action="append",
        choices=sorted(PARSERS),
        help="only read logs from this agent (repeatable)",
    )
    common.add_argument("--model", help="only models whose name contains this")
    common.add_argument("--project", help="only projects whose name contains this")
    common.add_argument(
        "--tz",
        type=_zone,
        help="IANA timezone for day boundaries (default: local time)",
    )
    common.add_argument(
        "--sort",
        choices=["key", "cost", "tokens"],
        default="key",
        help="row order (cost and tokens sort descending)",
    )
    common.add_argument("--limit", type=int, metavar="N", help="show only the first N rows")
    common.add_argument(
        "--format",
        choices=["table", "json", "csv"],
        default="table",
        help="output format",
    )
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
    cfg = sub.add_parser("config", help="show or create the config file")
    cfg.add_argument("action", choices=["path", "init", "show"], nargs="?", default="path")
    for name in REPORTS:
        report = sub.add_parser(name, parents=[common])
        if config:
            _apply_defaults(report, config.defaults)
    return parser


def _apply_defaults(parser: argparse.ArgumentParser, defaults: dict[str, Any]) -> None:
    """Use config values as option defaults, validated like command line input."""
    actions = {a.dest: a for a in parser._actions}
    for name, value in defaults.items():
        action = actions.get(name)
        if action is None or name in ("help", "since", "until", "svg"):
            raise ConfigError(f"unknown option in [defaults]: {name}")
        values = value if isinstance(value, list) else [value]
        if action.choices is not None and any(v not in action.choices for v in values):
            raise ConfigError(f"invalid value for {name} in [defaults]: {value!r}")
    parser.set_defaults(**defaults)


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


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv or argv[0] not in COMMANDS and argv[0] not in ("-h", "--help", "--version"):
        argv.insert(0, "daily")
    try:
        config = load_config()
        parser = build_parser(config)
    except ConfigError as exc:
        print(f"tokentally: config error: {exc}", file=sys.stderr)
        return 2
    args = parser.parse_args(argv)
    if args.command == "config":
        return config_command(args.action)
    key, title = REPORTS[args.command]
    tz = args.tz
    records = filter_records(
        load_records(args.source or PARSERS, config.paths),
        since=args.since,
        until=args.until,
        model=args.model,
        project=args.project,
        tz=tz,
    )
    prices = {**PRICES, **config.prices}
    grand = total(records, prices)
    groups = sort_groups(group(records, key, prices, tz=tz), args.sort)
    if args.limit is not None:
        groups = dict(list(groups.items())[: args.limit])
    rows = metric_rows(groups, args.metric)
    value_fmt = metric_format(args.metric)
    if args.svg:
        render_svg = column_chart_svg if key in TIME_KEYS else bar_chart_svg
        args.svg.write_text(
            render_svg(
                rows,
                f"{title} by {args.metric}",
                value_fmt,
                theme=THEMES[args.svg_theme],
            ),
            encoding="utf-8",
        )
    if args.format == "json":
        print(to_json(groups, key, grand))
        return 0
    if args.format == "csv":
        print(to_csv(groups, key), end="")
        return 0
    console = Console()
    console.print(totals_table(groups, title, grand))
    if args.chart:
        width = max(console.width - 40, 10)
        for line in bar_chart(rows, width, value_fmt):
            console.print(line, highlight=False)
    return 0
