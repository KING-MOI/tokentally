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
) -> list[UsageRecord]:
    """Keep records whose local date falls within [since, until]."""
    out = []
    for rec in records:
        day = rec.timestamp.astimezone(tz).date()
        if since and day < since:
            continue
        if until and day > until:
            continue
        out.append(rec)
    return out
