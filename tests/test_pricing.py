from datetime import UTC, datetime

import pytest

from tokentally.models import UsageRecord
from tokentally.pricing import Price, find_price, record_cost


def rec(model: str, **tokens: int) -> UsageRecord:
    return UsageRecord(
        source="claude",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
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


@pytest.mark.parametrize(
    ("model", "expected"),
    [
        ("claude-opus-5-5", "claude-opus-5-5"),
        ("claude-opus-5", "claude-opus-5"),
        ("claude-opus-4-1-20250805", "claude-opus-4-1"),
        ("claude-opus-4-20250514", "claude-opus-4"),
        ("gpt-5-codex", "gpt-5-codex"),
        ("gpt-5-2025-08-07", "gpt-5"),
        ("gemini-2.5-flash-lite", "gemini-2.5-flash-lite"),
        ("gemini-2.5-flash-preview-05-20", "gemini-2.5-flash"),
    ],
)
def test_most_specific_entry_wins(model: str, expected: str) -> None:
    from tokentally.pricing import PRICES

    assert find_price(model) is PRICES[expected]


def test_unpriced_models_are_reported_once() -> None:
    from tokentally.pricing import unpriced_models

    assert unpriced_models(["x", "claude-sonnet-4-5", "x", "a"]) == ["a", "x"]


def test_one_hour_cache_writes_cost_twice_the_input_rate() -> None:
    table = {"m": Price(input=2, output=0, cache_write=2.5, cache_read=0)}
    r = rec("m", cache_creation_tokens=3_000_000, cache_creation_1h_tokens=2_000_000)
    assert record_cost(r, table) == pytest.approx(1 * 2.5 + 2 * 4)


def test_cache_savings() -> None:
    from tokentally.pricing import cache_savings

    table = {"m": Price(input=3, output=15, cache_write=3.75, cache_read=0.3)}
    assert cache_savings(rec("m", cache_read_tokens=1_000_000), table) == pytest.approx(2.7)
    assert cache_savings(rec("unknown", cache_read_tokens=1_000_000), table) == 0.0


def test_vertex_and_gemini_api_paths_are_stripped() -> None:
    assert find_price("models/gemini-2.5-pro") == find_price("gemini-2.5-pro")
    assert find_price("publishers/anthropic/models/claude-opus-4-1@20250805") == find_price(
        "claude-opus-4-1"
    )


def test_long_context_rates_apply_above_the_threshold() -> None:
    long = Price(input=6, output=22.5)
    table = {"m": Price(input=3, output=15, long=long)}
    short = rec("m", input_tokens=200_000, output_tokens=1_000_000)
    big = rec("m", input_tokens=150_000, cache_read_tokens=50_001, output_tokens=1_000_000)
    assert record_cost(short, table) == pytest.approx(0.6 + 15)
    assert record_cost(big, table) == pytest.approx(0.9 + 22.5)
