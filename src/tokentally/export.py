"""Machine-readable report output."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from tokentally.aggregate import Totals
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


def to_csv(groups: dict[str, Totals], key_name: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([key_name, *FIELDS])
    for key, t in groups.items():
        d = totals_dict(t)
        writer.writerow([key, *(d[name] for name in FIELDS)])
    return buf.getvalue()


def summary_json(s: Summary) -> str:
    return json.dumps(
        {
            "first_day": s.first_day.isoformat() if s.first_day else None,
            "last_day": s.last_day.isoformat() if s.last_day else None,
            "active_days": s.active_days,
            "cost_per_active_day": round(s.cost_per_active_day, 6),
            "cache_hit_rate": round(s.cache_hit_rate, 4),
            "top_model": s.top_model,
            "top_project": s.top_project,
            "daily_cost": [round(c, 6) for c in s.daily_cost],
            "total": totals_dict(s.totals),
        },
        indent=2,
    )
