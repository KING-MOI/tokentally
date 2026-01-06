"""Per-model token prices and cost estimation.

Prices are USD per million tokens. They are estimates for local reporting and
can be overridden from the config file.
"""

from __future__ import annotations

from dataclasses import dataclass

from tokentally.models import UsageRecord


@dataclass(frozen=True, slots=True)
class Price:
    input: float
    output: float
    cache_write: float = 0.0
    cache_read: float = 0.0


PRICES: dict[str, Price] = {
    "claude-sonnet-4-5": Price(3.00, 15.00, 3.75, 0.30),
    "claude-opus-4-1": Price(15.00, 75.00, 18.75, 1.50),
}


def find_price(model: str, table: dict[str, Price] = PRICES) -> Price | None:
    """Look up a model's price, ignoring date suffixes like ``-20250929``."""
    name = model.lower()
    if name in table:
        return table[name]
    candidates = [k for k in table if name.startswith(k) and name[len(k)] in "-@:"]
    best = max(candidates, key=len, default=None)
    return table[best] if best else None


def record_cost(record: UsageRecord, table: dict[str, Price] = PRICES) -> float:
    price = find_price(record.model, table)
    if price is None:
        return 0.0
    return (
        record.input_tokens * price.input
        + record.output_tokens * price.output
        + record.cache_creation_tokens * price.cache_write
        + record.cache_read_tokens * price.cache_read
    ) / 1_000_000
