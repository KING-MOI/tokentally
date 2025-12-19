"""Log parsers for each supported agent CLI."""

from __future__ import annotations

from collections.abc import Callable, Iterator
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers.claude import parse_claude_file
from tokentally.parsers.codex import parse_codex_file
from tokentally.parsers.gemini import parse_gemini_file

Parser = Callable[[Path], Iterator[UsageRecord]]

PARSERS: dict[str, Parser] = {
    "claude": parse_claude_file,
    "codex": parse_codex_file,
    "gemini": parse_gemini_file,
}
