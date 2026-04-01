"""Locate agent log files on disk."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers import PARSERS

PATTERNS: dict[str, str] = {
    "claude": "**/*.jsonl",
    "codex": "**/rollout-*.jsonl",
    "gemini": "*/chats/session-*.json",
}


def default_roots(source: str) -> list[Path]:
    home = Path.home()
    if source == "claude":
        env = os.environ.get("CLAUDE_CONFIG_DIR")
        if env:
            return [Path(p).expanduser() / "projects" for p in env.split(",") if p.strip()]
        return [home / ".claude" / "projects", home / ".config" / "claude" / "projects"]
    if source == "codex":
        codex_home = os.environ.get("CODEX_HOME")
        base = Path(codex_home).expanduser() if codex_home else home / ".codex"
        return [base / "sessions"]
    if source == "gemini":
        return [home / ".gemini" / "tmp"]
    raise ValueError(f"unknown source: {source}")


def find_logs(source: str, roots: list[Path] | None = None) -> list[Path]:
    """Return every log file for ``source`` under ``roots``, sorted."""
    pattern = PATTERNS[source]
    found: set[Path] = set()
    for root in roots if roots is not None else default_roots(source):
        if root.is_dir():
            found.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(found)


def load_records(
    sources: Iterable[str],
    roots: dict[str, list[Path]] | None = None,
) -> list[UsageRecord]:
    """Parse every log for the given sources, oldest record first.

    Resuming or forking a Claude Code session copies earlier messages into the
    new session's file, so the same response can appear in several files. Those
    copies share a message key and are kept only once.
    """
    records: list[UsageRecord] = []
    seen: set[str] = set()
    for source in sources:
        parse = PARSERS[source]
        for path in find_logs(source, (roots or {}).get(source)):
            try:
                parsed = list(parse(path))
            except OSError:
                continue
            for rec in parsed:
                if rec.message_key:
                    if rec.message_key in seen:
                        continue
                    seen.add(rec.message_key)
                records.append(rec)
    records.sort(key=lambda r: r.timestamp)
    return records


def describe_roots(
    sources: Iterable[str], roots: dict[str, list[Path]] | None = None
) -> list[tuple[str, Path, int | None]]:
    """List (source, root, file count) for each searched root; None if missing."""
    out: list[tuple[str, Path, int | None]] = []
    for source in sources:
        for root in (roots or {}).get(source) or default_roots(source):
            count = len(find_logs(source, [root])) if root.is_dir() else None
            out.append((source, root, count))
    return out
