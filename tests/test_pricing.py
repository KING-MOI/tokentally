from datetime import datetime, timezone

import pytest

from tokentally.models import UsageRecord
from tokentally.pricing import Price, find_price, record_cost


def rec(model: str, **tokens: int) -> UsageRecord:
    return UsageRecord(
        source="claude",
        timestamp=datetime(2026, 1, 1, tzinfo=timezone.utc),
        model=model,
        session_id="s",
        **tokens,
    )


def test_dated_model_id_matches_base_entry() -> None:
    assert find_price("claude-sonnet-4-5-20250929") == find_price("claude-sonnet-4-5")


def test_unknown_model_has_no_price_and_zero_cost() -> None:
    assert find_price("mystery-model") is None
    assert record_cost(rec("mystery-model", output_tokens=1000)) == 0.0


def test_cost_uses_each_token_bucket() -> None:
    table = {"m": Price(input=1, output=2, cache_write=3, cache_read=4)}
    r = rec(
        "m",
        input_tokens=1_000_000,
        output_tokens=1_000_000,
        cache_creation_tokens=1_000_000,
        cache_read_tokens=1_000_000,
    )
    assert record_cost(r, table) == pytest.approx(10.0)
