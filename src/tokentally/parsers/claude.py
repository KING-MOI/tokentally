"""Parser for Claude Code session logs (~/.claude/projects/*/*.jsonl)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers._util import as_int, entry_timestamp, iter_jsonl


def _project_name(entry: dict[str, object], path: Path) -> str:
    cwd = entry.get("cwd")
    if isinstance(cwd, str) and cwd:
        return Path(cwd).name
    return path.parent.name


def parse_claude_file(path: Path) -> Iterator[UsageRecord]:
    """Yield one record per API response in a Claude Code session log.

    Claude Code writes a separate line for every content block of a response
    (thinking, text, each tool call) and repeats the full usage object on each
    one. Counting lines would multiply tokens by the number of blocks, so lines
    are collapsed on (message id, request id).
    """
    seen: set[str] = set()
    for entry in iter_jsonl(path, needle='"usage"'):
        if entry.get("type") != "assistant" or entry.get("isApiErrorMessage"):
            continue
        message = entry.get("message")
        if not isinstance(message, dict):
            continue
        usage = message.get("usage")
        if not isinstance(usage, dict):
            continue
        model = message.get("model") or "unknown"
        if model == "<synthetic>":
            continue
        message_id = message.get("id")
        key = f"{message_id}:{entry.get('requestId', '')}" if message_id else ""
        if key:
            if key in seen:
                continue
            seen.add(key)
        creation = usage.get("cache_creation")
        one_hour = (
            as_int(creation.get("ephemeral_1h_input_tokens")) if isinstance(creation, dict) else 0
        )
        timestamp = entry_timestamp(entry)
        if timestamp is None:
            continue
        yield UsageRecord(
            source="claude",
            timestamp=timestamp,
            model=model,
            session_id=entry.get("sessionId") or path.stem,
            project=_project_name(entry, path),
            input_tokens=as_int(usage.get("input_tokens")),
            output_tokens=as_int(usage.get("output_tokens")),
            cache_creation_tokens=as_int(usage.get("cache_creation_input_tokens")),
            cache_read_tokens=as_int(usage.get("cache_read_input_tokens")),
            cache_creation_1h_tokens=one_hour,
            message_key=key,
        )
