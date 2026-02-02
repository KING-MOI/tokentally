"""Command line entry point."""

from __future__ import annotations

import argparse

from rich.console import Console

from tokentally import __version__
from tokentally.aggregate import group, total
from tokentally.discovery import load_records
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
    sub = parser.add_subparsers(dest="command")
    for name in REPORTS:
        sub.add_parser(name)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    command = args.command or "daily"
    key, title = REPORTS[command]
    records = load_records(PARSERS)
    console = Console()
    console.print(totals_table(group(records, key), title, total(records)))
    return 0
