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


def test_prefix_match_requires_a_separator() -> None:
    table = {"gpt-5": Price(1, 1)}
    assert find_price("gpt-5-2025-08-07", table) is not None
    assert find_price("gpt-50", table) is None


def test_lookup_is_case_insensitive_and_strips_provider_prefix() -> None:
    assert find_price("us.anthropic.claude-sonnet-4-5-20250929-v1:0") == find_price(
        "claude-sonnet-4-5"
    )
    assert find_price("Claude-Sonnet-4-5") is not None
