"""Helpers shared by the log parsers."""

from __future__ import annotations

import json
from collections.abc import Iterator
from datetime import datetime, timezone
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


def parse_timestamp(value: str) -> datetime:
    """Parse an ISO 8601 timestamp, treating naive values as UTC."""
    ts = datetime.fromisoformat(value)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts
