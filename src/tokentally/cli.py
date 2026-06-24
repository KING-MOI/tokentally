"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from datetime import date, tzinfo
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from tokentally import __version__
from tokentally.commands import (
    CliError,
    blocks_command,
    config_command,
    paths_command,
    pricing_command,
    records_command,
    run_report,
    summary_command,
)
from tokentally.config import (
    Config,
    ConfigError,
    load_config,
)
from tokentally.filters import parse_date
from tokentally.parsers import PARSERS
from tokentally.svg import THEMES

REPORTS: dict[str, tuple[str, str]] = {
    "hourly": ("hour", "Hour"),
    "daily": ("day", "Date"),
    "weekly": ("week", "Week"),
    "monthly": ("month", "Month"),
    "models": ("model", "Model"),
    "sessions": ("session", "Session"),
    "projects": ("project", "Project"),
    "sources": ("source", "Source"),
    "branches": ("branch", "Branch"),
    "weekdays": ("weekday", "Weekday"),
    "hours": ("hour_of_day", "Hour"),
}


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
        choices=["model", "project", "source", "branch"],
        help="split each row by this field",
    )
    common.add_argument(
        "--json",
        dest="format",
        action="store_const",
        const="json",
        help="shorthand for --format json",
    )
    common.add_argument(
        "-o",
        "--output",
        type=Path,
        metavar="FILE",
        help="write json or csv output to FILE instead of stdout",
    )
    common.add_argument("--share", action="store_true", help="add a share-of-cost column")
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
        "--hours",
        type=_positive,
        default=5,
        help="window length in hours (default 5)",
    )
    blocks.add_argument(
        "--watch",
        type=float,
        nargs="?",
        const=10.0,
        metavar="SECONDS",
        help="redraw every SECONDS (default 10) until ctrl-c",
    )
    reports = []
    for name, spec in REPORTS.items():
        report = sub.add_parser(name, parents=[common])
        report.set_defaults(report=spec)
        reports.append(report)
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
        return records_command(args, config)
    return run_report(args, config)
