"""On-disk cache of parsed records, keyed by log file size and mtime.

Session logs only grow, and most of them stop changing once a session ends.
Re-reading gigabytes of them on every run is the slow part of a report, so
parsed records are stored per file and reused while the file is unchanged.
"""

from __future__ import annotations

import json
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


class FileCache:
    """Parsed records per log file, valid while size and mtime are unchanged."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.entries: dict[str, dict[str, Any]] = {}
        self.dirty = False
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if isinstance(raw, dict) and raw.get("version") == VERSION:
            self.entries = raw.get("files", {})

    def get(self, log: Path) -> list[UsageRecord] | None:
        entry = self.entries.get(str(log))
        if entry is None:
            return None
        st = log.stat()
        if entry["size"] != st.st_size or entry["mtime_ns"] != st.st_mtime_ns:
            return None
        try:
            return [decode(v) for v in entry["records"]]
        except (TypeError, ValueError, KeyError):
            return None

    def put(self, log: Path, records: list[UsageRecord]) -> None:
        st = log.stat()
        self.entries[str(log)] = {
            "size": st.st_size,
            "mtime_ns": st.st_mtime_ns,
            "records": [encode(r) for r in records],
        }
        self.dirty = True

    def save(self) -> None:
        if not self.dirty:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps({"version": VERSION, "files": self.entries}), encoding="utf-8")
        os.replace(tmp, self.path)
        self.dirty = False
