"""Group usage records into totals."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass

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


KeyFn = Callable[[UsageRecord], str]

KEYS: dict[str, KeyFn] = {
    "day": lambda r: r.timestamp.date().isoformat(),
    "model": lambda r: r.model,
}


def group(
    records: Iterable[UsageRecord],
    by: str,
    prices: dict[str, Price] = PRICES,
) -> dict[str, Totals]:
    """Sum records into one Totals per key, sorted by key."""
    key_fn = KEYS[by]
    out: dict[str, Totals] = {}
    for rec in records:
        out.setdefault(key_fn(rec), Totals()).add(rec, record_cost(rec, prices))
    return dict(sorted(out.items()))
