"""Group usage records into totals."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass
from datetime import datetime, tzinfo

from tokentally.models import UsageRecord
from tokentally.pricing import PRICES, Price, record_cost


@dataclass(slots=True)
class Totals:
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cost: float = 0.0
    requests: int = 0
    first_seen: datetime | None = None
    last_seen: datetime | None = None

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
        )

    def add(self, record: UsageRecord, cost: float) -> None:
        self.input_tokens += record.input_tokens
        self.output_tokens += record.output_tokens
        self.cache_creation_tokens += record.cache_creation_tokens
        self.cache_read_tokens += record.cache_read_tokens
        self.cost += cost
        self.requests += 1
        ts = record.timestamp
        if self.first_seen is None or ts < self.first_seen:
            self.first_seen = ts
        if self.last_seen is None or ts > self.last_seen:
            self.last_seen = ts


KeyFn = Callable[[UsageRecord, datetime], str]

KEYS: dict[str, KeyFn] = {
    "day": lambda r, t: t.date().isoformat(),
    "month": lambda r, t: t.strftime("%Y-%m"),
    "week": lambda r, t: f"{t.isocalendar().year}-W{t.isocalendar().week:02d}",
    "model": lambda r, t: r.model,
    "session": lambda r, t: r.session_id,
    "project": lambda r, t: r.project or "(none)",
    "source": lambda r, t: r.source,
}


def group(
    records: Iterable[UsageRecord],
    by: str,
    prices: dict[str, Price] = PRICES,
    tz: tzinfo | None = None,
) -> dict[str, Totals]:
    """Sum records into one Totals per key, sorted by key.

    Calendar keys are computed in ``tz``; ``None`` means the machine's local
    zone, since "what did I spend today" is a local-time question and log
    timestamps are UTC.
    """
    key_fn = KEYS[by]
    out: dict[str, Totals] = {}
    for rec in records:
        key = key_fn(rec, rec.timestamp.astimezone(tz))
        out.setdefault(key, Totals()).add(rec, record_cost(rec, prices))
    return dict(sorted(out.items()))


def sort_groups(groups: dict[str, Totals], by: str = "key") -> dict[str, Totals]:
    """Reorder groups by key, or descending by ``cost``/``tokens``."""
    if by == "key":
        return dict(sorted(groups.items()))
    if by == "cost":
        return dict(sorted(groups.items(), key=lambda kv: kv[1].cost, reverse=True))
    if by == "tokens":
        return dict(sorted(groups.items(), key=lambda kv: kv[1].total_tokens, reverse=True))
    raise ValueError(f"cannot sort by {by!r}")


def total(records: Iterable[UsageRecord], prices: dict[str, Price] = PRICES) -> Totals:
    """Sum every record into a single Totals."""
    out = Totals()
    for rec in records:
        out.add(rec, record_cost(rec, prices))
    return out
