"""Group usage into fixed-length billing windows.

Claude subscription limits reset on rolling five hour windows that open with
the first message after the previous window has closed. Seeing usage per
window answers "how much of this window have I used".
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import datetime, timedelta

from tokentally.aggregate import Totals
from tokentally.models import UsageRecord
from tokentally.pricing import PRICES, Price, record_cost

WINDOW = timedelta(hours=5)


@dataclass(slots=True)
class Block:
    start: datetime
    totals: Totals = field(default_factory=Totals)
    length: timedelta = WINDOW

    @property
    def end(self) -> datetime:
        return self.start + self.length


def billing_blocks(
    records: Iterable[UsageRecord],
    prices: dict[str, Price] = PRICES,
    length: timedelta = WINDOW,
) -> list[Block]:
    """Split time-ordered records into windows starting on the hour."""
    blocks: list[Block] = []
    for rec in sorted(records, key=lambda r: r.timestamp):
        if not blocks or rec.timestamp >= blocks[-1].end:
            start = rec.timestamp.replace(minute=0, second=0, microsecond=0)
            blocks.append(Block(start=start, length=length))
        blocks[-1].totals.add(rec, record_cost(rec, prices))
    return blocks
