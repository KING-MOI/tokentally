"""Command line entry point."""

from __future__ import annotations

import argparse
import sys
from datetime import tzinfo
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from rich.console import Console

from tokentally import __version__
from tokentally.aggregate import group, sort_groups, total
from tokentally.charts import bar_chart
from tokentally.discovery import load_records
from tokentally.export import to_csv, to_json
from tokentally.filters import filter_records, parse_date
from tokentally.fmt import human_tokens, money
from tokentally.parsers import PARSERS
from tokentally.render import metric_rows, totals_table

REPORTS: dict[str, tuple[str, str]] = {
    "daily": ("day", "Date"),
    "weekly": ("week", "Week"),
    "monthly": ("month", "Month"),
    "models": ("model", "Model"),
    "sessions": ("session", "Session"),
    "projects": ("project", "Project"),
    "sources": ("source", "Source"),
}


def _zone(name: str) -> tzinfo:
    try:
        return ZoneInfo(name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise argparse.ArgumentTypeError(f"unknown timezone: {name}") from exc


def build_parser() -> argparse.ArgumentParser:
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
    sub = parser.add_subparsers(dest="command")
    for name in REPORTS:
        sub.add_parser(name, parents=[common])
    return parser


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv or argv[0] not in REPORTS and argv[0] not in ("-h", "--help", "--version"):
        argv.insert(0, "daily")
    args = build_parser().parse_args(argv)
    key, title = REPORTS[args.command]
    tz = args.tz
    records = filter_records(
        load_records(args.source or PARSERS),
        since=args.since,
        until=args.until,
        model=args.model,
        project=args.project,
        tz=tz,
    )
    grand = total(records)
    groups = sort_groups(group(records, key, tz=tz), args.sort)
    if args.limit is not None:
        groups = dict(list(groups.items())[: args.limit])
    if args.format == "json":
        print(to_json(groups, key, grand))
        return 0
    if args.format == "csv":
        print(to_csv(groups, key), end="")
        return 0
    console = Console()
    console.print(totals_table(groups, title, grand))
    if args.chart:
        value_fmt = money if args.metric == "cost" else (lambda v: human_tokens(int(v)))
        width = max(console.width - 40, 10)
        for line in bar_chart(metric_rows(groups, args.metric), width, value_fmt):
            console.print(line, highlight=False)
    return 0
