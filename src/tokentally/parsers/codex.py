"""Parser for Codex CLI rollout logs (~/.codex/sessions/YYYY/MM/DD/*.jsonl)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers._util import as_int, iter_jsonl, parse_timestamp


def parse_codex_file(path: Path) -> Iterator[UsageRecord]:
    """Yield one record per token_count event in a Codex rollout.

    Codex reports ``input_tokens`` inclusive of ``cached_input_tokens``, so the
    cached part is split out to keep it from being billed twice.
    """
    session_id = path.stem
    model = "unknown"
    for entry in iter_jsonl(path):
        kind = entry.get("type")
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        if kind == "session_meta":
            session_id = payload.get("id") or session_id
        elif kind == "turn_context":
            model = payload.get("model") or model
        elif kind == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info")
            if not isinstance(info, dict):
                continue
            last = info.get("last_token_usage")
            if not isinstance(last, dict):
                continue
            cached = as_int(last.get("cached_input_tokens"))
            yield UsageRecord(
                source="codex",
                timestamp=parse_timestamp(entry["timestamp"]),
                model=model,
                session_id=session_id,
                input_tokens=max(as_int(last.get("input_tokens")) - cached, 0),
                output_tokens=as_int(last.get("output_tokens")),
                cache_read_tokens=cached,
            )
