from __future__ import annotations

from datetime import UTC, datetime, timezone

from tokentally.models import UsageRecord


def make_record(
    when: str = "2026-03-01T12:00:00",
    model: str = "claude-sonnet-4-5",
    session_id: str = "s1",
    project: str = "acme",
    source: str = "claude",
    **tokens: int,
) -> UsageRecord:
    ts = datetime.fromisoformat(when)
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=UTC)
    return UsageRecord(
        source=source,
        timestamp=ts,
        model=model,
        session_id=session_id,
        project=project,
        **tokens,
    )
