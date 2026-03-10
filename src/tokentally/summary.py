"""Headline numbers for the summary command."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from datetime import date, tzinfo

from tokentally.aggregate import Totals, daily_series, group, sort_groups, total
from tokentally.models import UsageRecord
from tokentally.pricing import PRICES, Price


@dataclass(slots=True)
class Summary:
    totals: Totals
    first_day: date | None
    last_day: date | None
    active_days: int
    daily_cost: list[float]
    top_model: str | None
    top_project: str | None

    @property
    def cost_per_active_day(self) -> float:
        return self.totals.cost / self.active_days if self.active_days else 0.0

    @property
    def cache_hit_rate(self) -> float:
        """Share of prompt tokens served from cache."""
        t = self.totals
        prompt = t.input_tokens + t.cache_creation_tokens + t.cache_read_tokens
        return t.cache_read_tokens / prompt if prompt else 0.0


def summarize(
    records: Sequence[UsageRecord],
    prices: dict[str, Price] = PRICES,
    tz: tzinfo | None = None,
) -> Summary:
    days = group(records, "day", prices, tz=tz)
    first = date.fromisoformat(next(iter(days))) if days else None
    last = date.fromisoformat(list(days)[-1]) if days else None
    series = daily_series(days, first, last) if first and last else []
    models = sort_groups(group(records, "model", prices, tz=tz), "cost")
    projects = sort_groups(group(records, "project", prices, tz=tz), "cost")
    return Summary(
        totals=total(records, prices),
        first_day=first,
        last_day=last,
        active_days=len(days),
        daily_cost=[t.cost for _, t in series],
        top_model=next(iter(models), None),
        top_project=next(iter(projects), None),
    )
