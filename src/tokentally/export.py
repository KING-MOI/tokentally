"""Machine-readable report output."""

from __future__ import annotations

import csv
import io
import json
from collections.abc import Iterable, Iterator
from typing import Any

from tokentally.aggregate import Totals
from tokentally.models import UsageRecord
from tokentally.pricing import Price, record_cost
from tokentally.summary import Summary

FIELDS = [
    "input_tokens",
    "output_tokens",
    "cache_creation_tokens",
    "cache_read_tokens",
    "total_tokens",
    "requests",
    "cost",
]


def totals_dict(t: Totals) -> dict[str, Any]:
    out: dict[str, Any] = {name: getattr(t, name) for name in FIELDS}
    out["cost"] = round(t.cost, 6)
    return out


def to_json(
    groups: dict[str, Totals],
    key_name: str,
    grand: Totals,
    sub_rows: dict[str, dict[str, Totals]] | None = None,
    sub_name: str = "",
) -> str:
    rows = []
    for key, t in groups.items():
        row: dict[str, Any] = {key_name: key, **totals_dict(t)}
        if sub_rows is not None:
            row["breakdown"] = [
                {sub_name: child, **totals_dict(ct)} for child, ct in sub_rows.get(key, {}).items()
            ]
        rows.append(row)
    return json.dumps({"rows": rows, "total": totals_dict(grand)}, indent=2)


def to_csv(
    groups: dict[str, Totals],
    key_name: str,
    sub_rows: dict[str, dict[str, Totals]] | None = None,
    sub_name: str = "",
) -> str:
    """CSV with one row per group; a breakdown adds a column and long-format rows."""
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    if sub_rows is None:
        writer.writerow([key_name, *FIELDS])
        for key, t in groups.items():
            d = totals_dict(t)
            writer.writerow([key, *(d[name] for name in FIELDS)])
        return buf.getvalue()
    writer.writerow([key_name, sub_name, *FIELDS])
    for key in groups:
        for child, ct in sub_rows.get(key, {}).items():
            d = totals_dict(ct)
            writer.writerow([key, child, *(d[name] for name in FIELDS)])
    return buf.getvalue()


def summary_json(s: Summary) -> str:
    return json.dumps(
        {
            "first_day": s.first_day.isoformat() if s.first_day else None,
            "last_day": s.last_day.isoformat() if s.last_day else None,
            "active_days": s.active_days,
            "cost_per_active_day": round(s.cost_per_active_day, 6),
            "cache_hit_rate": round(s.cache_hit_rate, 4),
            "cache_savings": round(s.cache_savings, 6),
            "today_cost": round(s.today_cost, 6),
            "month_cost": round(s.month_cost, 6),
            "busiest_day": s.busiest_day,
            "tokens_per_request": round(s.tokens_per_request, 2),
            "top_model": s.top_model,
            "top_project": s.top_project,
            "daily_cost": [round(c, 6) for c in s.daily_cost],
            "total": totals_dict(s.totals),
        },
        indent=2,
    )


def records_jsonl(records: Iterable[UsageRecord], prices: dict[str, Price]) -> Iterator[str]:
    """One JSON line per record, with its estimated cost."""
    for r in records:
        yield json.dumps(
            {
                "timestamp": r.timestamp.isoformat(),
                "source": r.source,
                "model": r.model,
                "session_id": r.session_id,
                "project": r.project,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "cache_creation_tokens": r.cache_creation_tokens,
                "cache_read_tokens": r.cache_read_tokens,
                "cost": round(record_cost(r, prices), 8),
            }
        )
