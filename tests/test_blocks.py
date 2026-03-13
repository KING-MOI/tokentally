from datetime import timedelta

from conftest import make_record
from tokentally.blocks import billing_blocks


def test_records_within_five_hours_share_a_block() -> None:
    records = [
        make_record("2026-03-01T09:40:00", output_tokens=1),
        make_record("2026-03-01T13:59:00", output_tokens=2),
        make_record("2026-03-01T14:00:00", output_tokens=4),
    ]
    blocks = billing_blocks(records)
    assert [b.start.hour for b in blocks] == [9, 14]
    assert [b.totals.output_tokens for b in blocks] == [3, 4]


def test_block_after_a_long_gap_starts_on_its_own_hour() -> None:
    records = [make_record("2026-03-01T01:10:00"), make_record("2026-03-02T22:30:00")]
    blocks = billing_blocks(records)
    assert [(b.start.day, b.start.hour) for b in blocks] == [(1, 1), (2, 22)]
    assert blocks[1].end - blocks[1].start == timedelta(hours=5)


def test_input_order_does_not_matter() -> None:
    records = [make_record("2026-03-01T12:00:00"), make_record("2026-03-01T09:00:00")]
    assert len(billing_blocks(records)) == 1


def test_projection_extrapolates_burn_rate() -> None:
    from datetime import datetime

    from tokentally.blocks import is_active, projected_cost

    rec = make_record("2026-03-01T10:00:00", model="claude-opus-4-1", output_tokens=100_000)
    (block,) = billing_blocks([rec])
    now = datetime.fromisoformat("2026-03-01T11:00:00+00:00")
    assert is_active(block, now)
    assert projected_cost(block, now) == block.totals.cost * 5
    assert not is_active(block, now + timedelta(hours=4))


def test_finished_block_projects_its_actual_cost() -> None:
    from datetime import datetime

    from tokentally.blocks import projected_cost

    (block,) = billing_blocks([make_record("2026-03-01T10:00:00", output_tokens=10)])
    later = datetime.fromisoformat("2026-03-02T00:00:00+00:00")
    assert projected_cost(block, later) == block.totals.cost
