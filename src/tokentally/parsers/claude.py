"""Parser for Claude Code session logs (~/.claude/projects/*/*.jsonl)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers._util import iter_jsonl, parse_timestamp


def parse_claude_file(path: Path) -> Iterator[UsageRecord]:
    for entry in iter_jsonl(path):
        if entry.get("type") != "assistant":
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        yield UsageRecord(
            source="claude",
            timestamp=parse_timestamp(entry["timestamp"]),
            model=message.get("model", "unknown"),
            session_id=entry.get("sessionId", ""),
            input_tokens=usage.get("input_tokens", 0),
            output_tokens=usage.get("output_tokens", 0),
            cache_creation_tokens=usage.get("cache_creation_input_tokens", 0),
            cache_read_tokens=usage.get("cache_read_input_tokens", 0),
        )
