from datetime import UTC, datetime

from tokentally.models import UsageRecord


def test_total_tokens_sums_every_bucket() -> None:
    rec = UsageRecord(
        source="claude",
        timestamp=datetime(2026, 1, 1, tzinfo=UTC),
        model="claude-sonnet-4-5",
        session_id="s1",
        input_tokens=10,
        output_tokens=20,
        cache_creation_tokens=30,
        cache_read_tokens=40,
    )
    assert rec.total_tokens == 100
