"""On-disk cache of parsed records, keyed by log file size and mtime.

Session logs only grow, and most of them stop changing once a session ends.
Re-reading gigabytes of them on every run is the slow part of a report, so
parsed records are stored per file and reused while the file is unchanged.
"""

from __future__ import annotations

import os
from dataclasses import astuple, fields
from datetime import datetime
from pathlib import Path
from typing import Any

from tokentally.models import UsageRecord

VERSION = 1
FIELDS = [f.name for f in fields(UsageRecord)]


def cache_path() -> Path:
    base = os.environ.get("XDG_CACHE_HOME")
    root = Path(base).expanduser() if base else Path.home() / ".cache"
    return root / "tokentally" / "records.json"


def encode(record: UsageRecord) -> list[Any]:
    values = list(astuple(record))
    values[FIELDS.index("timestamp")] = record.timestamp.isoformat()
    return values


def decode(values: list[Any]) -> UsageRecord:
    data = dict(zip(FIELDS, values, strict=True))
    data["timestamp"] = datetime.fromisoformat(data["timestamp"])
    return UsageRecord(**data)
