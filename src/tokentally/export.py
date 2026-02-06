"""Machine-readable report output."""

from __future__ import annotations

import csv
import io
import json
from typing import Any

from tokentally.aggregate import Totals

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


def to_json(groups: dict[str, Totals], key_name: str, grand: Totals) -> str:
    rows = [{key_name: key, **totals_dict(t)} for key, t in groups.items()]
    return json.dumps({"rows": rows, "total": totals_dict(grand)}, indent=2)


def to_csv(groups: dict[str, Totals], key_name: str) -> str:
    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([key_name, *FIELDS])
    for key, t in groups.items():
        d = totals_dict(t)
        writer.writerow([key, *(d[name] for name in FIELDS)])
    return buf.getvalue()
