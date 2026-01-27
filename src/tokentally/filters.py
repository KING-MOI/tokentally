"""Record filtering and date argument parsing."""

from __future__ import annotations

import re
from collections.abc import Iterable
from datetime import date, timedelta, tzinfo

from tokentally.models import UsageRecord


def parse_date(value: str, today: date | None = None) -> date:
    """Parse ``YYYY-MM-DD``, ``YYYYMMDD``, ``today``, ``yesterday`` or ``Nd``."""
    today = today or date.today()
    text = value.strip().lower()
    if text == "today":
        return today
    if text == "yesterday":
        return today - timedelta(days=1)
    rel = re.fullmatch(r"(\d+)([dw])", text)
    if rel:
        n = int(rel.group(1)) * (7 if rel.group(2) == "w" else 1)
        return today - timedelta(days=n)
    if re.fullmatch(r"\d{8}", text):
        return date(int(text[:4]), int(text[4:6]), int(text[6:]))
    return date.fromisoformat(text)


def filter_records(
    records: Iterable[UsageRecord],
    since: date | None = None,
    until: date | None = None,
    tz: tzinfo | None = None,
    sources: Iterable[str] | None = None,
    model: str | None = None,
    project: str | None = None,
) -> list[UsageRecord]:
    """Keep records matching every given condition.

    Dates are compared on the record's local date and are inclusive. ``model``
    and ``project`` are case-insensitive substring matches.
    """
    wanted_sources = set(sources) if sources is not None else None
    model_q = model.lower() if model else None
    project_q = project.lower() if project else None
    out = []
    for rec in records:
        if wanted_sources is not None and rec.source not in wanted_sources:
            continue
        if model_q and model_q not in rec.model.lower():
            continue
        if project_q and project_q not in rec.project.lower():
            continue
        day = rec.timestamp.astimezone(tz).date()
        if since and day < since:
            continue
        if until and day > until:
            continue
        out.append(rec)
    return out
