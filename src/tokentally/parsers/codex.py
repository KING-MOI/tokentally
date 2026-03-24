"""Parser for Codex CLI rollout logs (~/.codex/sessions/YYYY/MM/DD/*.jsonl)."""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

from tokentally.models import UsageRecord
from tokentally.parsers._util import as_int, entry_timestamp, iter_jsonl

FIELDS = ("input_tokens", "cached_input_tokens", "output_tokens")


def _delta(total: object, previous: object) -> dict[str, int] | None:
    """Per-turn usage from two running totals, for logs without last_token_usage."""
    if not isinstance(total, dict):
        return None
    prev = previous if isinstance(previous, dict) else {}
    return {f: max(as_int(total.get(f)) - as_int(prev.get(f)), 0) for f in FIELDS}


def parse_codex_file(path: Path) -> Iterator[UsageRecord]:
    """Yield one record per token_count event in a Codex rollout.

    Codex reports ``input_tokens`` inclusive of ``cached_input_tokens``, so the
    cached part is split out to keep it from being billed twice.

    Codex also re-emits the same token_count event (for example after a rate
    limit refresh). Those repeats leave ``total_token_usage`` unchanged, which is
    how they are told apart from a genuinely identical turn.
    """
    session_id = path.stem
    model = "unknown"
    project = ""
    last_total: object = None
    for entry in iter_jsonl(path):
        kind = entry.get("type")
        payload = entry.get("payload")
        if not isinstance(payload, dict):
            continue
        if kind == "session_meta":
            session_id = payload.get("id") or session_id
            cwd = payload.get("cwd")
            if isinstance(cwd, str) and cwd:
                project = Path(cwd).name
        elif kind == "turn_context":
            model = payload.get("model") or model
        elif kind == "event_msg" and payload.get("type") == "token_count":
            info = payload.get("info")
            if not isinstance(info, dict):
                continue
            total = info.get("total_token_usage")
            if total is not None and total == last_total:
                continue
            last = info.get("last_token_usage")
            if not isinstance(last, dict):
                last = _delta(total, last_total)
            last_total = total
            if last is None:
                continue
            cached = as_int(last.get("cached_input_tokens"))
            timestamp = entry_timestamp(entry)
            if timestamp is None:
                continue
            yield UsageRecord(
                source="codex",
                timestamp=timestamp,
                model=model,
                session_id=session_id,
                project=project,
                input_tokens=max(as_int(last.get("input_tokens")) - cached, 0),
                output_tokens=as_int(last.get("output_tokens")),
                cache_read_tokens=cached,
            )
