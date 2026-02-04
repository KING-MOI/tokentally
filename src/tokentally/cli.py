"""Command line entry point."""

from __future__ import annotations

import argparse

from rich.console import Console

from tokentally import __version__
from tokentally.aggregate import group, total
from tokentally.discovery import load_records
from tokentally.filters import filter_records, parse_date
from tokentally.parsers import PARSERS
from tokentally.render import totals_table

REPORTS: dict[str, tuple[str, str]] = {
    "daily": ("day", "Date"),
    "weekly": ("week", "Week"),
    "monthly": ("month", "Month"),
    "models": ("model", "Model"),
    "sessions": ("session", "Session"),
    "projects": ("project", "Project"),
    "sources": ("source", "Source"),
}


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
    sub = parser.add_subparsers(dest="command")
    for name in REPORTS:
        sub.add_parser(name, parents=[common])
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "daily"
    key, title = REPORTS[command]
    records = filter_records(
        load_records(getattr(args, "source", None) or PARSERS),
        since=getattr(args, "since", None),
        until=getattr(args, "until", None),
        model=getattr(args, "model", None),
        project=getattr(args, "project", None),
    )
    console = Console()
    console.print(totals_table(group(records, key), title, total(records)))
    return 0
