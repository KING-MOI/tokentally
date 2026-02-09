"""Helpers shared by the log parsers."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import UTC, datetime, timezone
from pathlib import Path
from typing import Any


def iter_jsonl(path: Path) -> Iterator[dict[str, Any]]:
    """Yield each JSON object in a JSONL file.

    Agents append to these files while they run, so a truncated last line or a
    stray non-object line is normal. Both are skipped instead of aborting the
    whole report.
    """
    with path.open(encoding="utf-8") as fh:
        for line in fh:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                yield obj


def as_int(value: Any) -> int:
    """Coerce a token count from a log field; null or garbage counts as 0."""
    if isinstance(value, bool):
        return 0
    if isinstance(value, int):
        return max(value, 0)
    if isinstance(value, float):
        return max(int(value), 0)
    return 0


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, treating naive values as UTC."""
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return ts


def entry_timestamp(entry: dict[str, Any]) -> datetime | None:
    """Return the entry's ``timestamp`` field parsed, or None if unusable."""
    raw = entry.get("timestamp")
    if not isinstance(raw, str):
        return None
    try:
        return parse_timestamp(raw)
    except ValueError:
        return None
