"""Per-model token prices and cost estimation.

Prices are USD per million tokens. They are estimates for local reporting and
can be overridden from the config file.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from tokentally.models import UsageRecord


@dataclass(frozen=True, slots=True)
class Price:
    """Rates in USD per million tokens.

    ``long`` holds the rates for requests whose prompt (input plus cache write
    plus cache read) exceeds ``long_threshold`` tokens, for models that charge
    more for long context.
    """

    input: float
    output: float
    cache_write: float = 0.0
    cache_read: float = 0.0
    long: Price | None = None
    long_threshold: int = 200_000


ANTHROPIC: dict[str, Price] = {
    "claude-3-5-haiku": Price(0.80, 4.00, 1.00, 0.08),
    "claude-3-5-sonnet": Price(3.00, 15.00, 3.75, 0.30),
    "claude-3-7-sonnet": Price(3.00, 15.00, 3.75, 0.30),
    "claude-3-haiku": Price(0.25, 1.25, 0.30, 0.03),
    "claude-3-opus": Price(15.00, 75.00, 18.75, 1.50),
    "claude-fable-5": Price(10.00, 50.00, 12.50, 1.00),
    "claude-fable-5-1": Price(10.00, 50.00, 12.50, 1.00),
    "claude-fable-5-2": Price(8.00, 40.00, 10.00, 0.20),
    "claude-haiku-4-5": Price(1.00, 5.00, 1.25, 0.10),
    "claude-haiku-5-5": Price(0.10, 0.50, 0.125, 0.01),
    "claude-opus-4": Price(15.00, 75.00, 18.75, 1.50),
    "claude-opus-4-1": Price(15.00, 75.00, 18.75, 1.50),
    "claude-opus-4-5": Price(5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-6": Price(5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-7": Price(5.00, 25.00, 6.25, 0.50),
    "claude-opus-4-8": Price(5.00, 25.00, 6.25, 0.50),
    "claude-opus-5": Price(5.00, 25.00, 6.25, 0.50),
    "claude-opus-5-5": Price(4.00, 20.00, 5.00, 0.20),
    "claude-sonnet-4": Price(3.00, 15.00, 3.75, 0.30, long=Price(6.00, 22.50, 7.50, 0.60)),
    "claude-sonnet-4-5": Price(3.00, 15.00, 3.75, 0.30, long=Price(6.00, 22.50, 7.50, 0.60)),
    "claude-sonnet-4-6": Price(3.00, 15.00, 3.75, 0.30),
    "claude-sonnet-5": Price(2.00, 10.00, 2.50, 0.20),
    "claude-sonnet-5-5": Price(2.00, 10.00, 2.50, 0.10),
}

OPENAI: dict[str, Price] = {
    "codex-mini-latest": Price(1.50, 6.00, 0.0, 0.375),
    "gpt-4.1": Price(2.00, 8.00, 0.0, 0.50),
    "gpt-4.1-mini": Price(0.40, 1.60, 0.0, 0.10),
    "gpt-4.1-nano": Price(0.10, 0.40, 0.0, 0.025),
    "gpt-4o": Price(2.50, 10.00, 0.0, 1.25),
    "gpt-4o-mini": Price(0.15, 0.60, 0.0, 0.075),
    "gpt-5": Price(1.25, 10.00, 0.0, 0.125),
    "gpt-5-codex": Price(1.25, 10.00, 0.0, 0.125),
    "gpt-5-mini": Price(0.25, 2.00, 0.0, 0.025),
    "gpt-5-nano": Price(0.05, 0.40, 0.0, 0.005),
    "gpt-5.1": Price(1.25, 10.00, 0.0, 0.125),
    "gpt-5.1-codex": Price(1.25, 10.00, 0.0, 0.125),
    "gpt-5.1-codex-mini": Price(0.25, 2.00, 0.0, 0.025),
    "o3": Price(2.00, 8.00, 0.0, 0.50),
    "o3-mini": Price(1.10, 4.40, 0.0, 0.55),
    "o4-mini": Price(1.10, 4.40, 0.0, 0.275),
}

GOOGLE: dict[str, Price] = {
    "gemini-2.0-flash": Price(0.10, 0.40, 0.0, 0.025),
    "gemini-2.5-flash": Price(0.30, 2.50, 0.0, 0.075),
    "gemini-2.5-flash-lite": Price(0.10, 0.40, 0.0, 0.025),
    "gemini-2.5-pro": Price(1.25, 10.00, 0.0, 0.31, long=Price(2.50, 15.00, 0.0, 0.625)),
    "gemini-3-pro-preview": Price(2.00, 12.00, 0.0, 0.20, long=Price(4.00, 18.00, 0.0, 0.40)),
}

PRICES: dict[str, Price] = {**ANTHROPIC, **OPENAI, **GOOGLE}


FAST_MULTIPLIER = 2.0
WEB_SEARCH_PER_REQUEST = 10.0 / 1000


def find_price(model: str, table: dict[str, Price] = PRICES) -> Price | None:
    """Look up a model's price, ignoring date suffixes like ``-20250929``."""
    name = model.lower().rsplit("/", 1)[-1]
    if "anthropic." in name:
        name = name.split("anthropic.", 1)[1]
    if name in table:
        return table[name]
    candidates = [k for k in table if name.startswith(k) and name[len(k)] in "-@:"]
    best = max(candidates, key=len, default=None)
    return table[best] if best else None


def record_cost(record: UsageRecord, table: dict[str, Price] = PRICES) -> float:
    price = find_price(record.model, table)
    if price is None:
        return 0.0
    prompt = record.input_tokens + record.cache_creation_tokens + record.cache_read_tokens
    if price.long is not None and prompt > price.long_threshold:
        price = price.long
    one_hour = min(record.cache_creation_1h_tokens, record.cache_creation_tokens)
    tokens = (
        record.input_tokens * price.input
        + record.output_tokens * price.output
        + (record.cache_creation_tokens - one_hour) * price.cache_write
        + one_hour * price.input * 2
        + record.cache_read_tokens * price.cache_read
    ) / 1_000_000
    if record.fast:
        tokens *= FAST_MULTIPLIER
    return tokens + record.web_searches * WEB_SEARCH_PER_REQUEST


def unpriced_models(models: Iterable[str], table: dict[str, Price] = PRICES) -> list[str]:
    """Return the distinct models that have no price, sorted."""
    return sorted({m for m in models if find_price(m, table) is None})


def cache_savings(record: UsageRecord, table: dict[str, Price] = PRICES) -> float:
    """What the record's cache reads saved versus paying the full input rate."""
    price = find_price(record.model, table)
    if price is None:
        return 0.0
    return record.cache_read_tokens * (price.input - price.cache_read) / 1_000_000
