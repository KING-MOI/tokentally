"""Parser for Gemini CLI chat recordings (~/.gemini/tmp/<hash>/chats/*.json).

Gemini CLI stores each session as one JSON document rather than JSONL.
"""

from __future__ import annotations

import json
from collections.abc import Iterator
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers._util import as_int, entry_timestamp


def parse_gemini_file(path: Path) -> Iterator[UsageRecord]:
    try:
        doc = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return
    if not isinstance(doc, dict):
        return
    session_id = doc.get("sessionId") or path.stem
    for message in doc.get("messages") or []:
        if not isinstance(message, dict) or message.get("type") != "gemini":
            continue
        tokens = message.get("tokens")
        if not isinstance(tokens, dict):
            continue
        timestamp = entry_timestamp(message)
        if timestamp is None:
            continue
        yield UsageRecord(
            source="gemini",
            timestamp=timestamp,
            model=message.get("model") or "unknown",
            session_id=session_id,
            input_tokens=as_int(tokens.get("input")),
            output_tokens=as_int(tokens.get("output")),
            cache_read_tokens=as_int(tokens.get("cached")),
        )
