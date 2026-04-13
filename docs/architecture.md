# Architecture

```
discovery.find_logs ──> parsers.<source> ──> UsageRecord ──> filters
                                                              │
                         pricing.record_cost <── aggregate.group / total
                                                              │
                         render (rich) / export (json, csv) / svg / charts
```

- `models.UsageRecord` is the only shape that crosses module boundaries. Every
  parser maps its agent's fields onto the same four token buckets.
- Parsers never raise on bad input. Broken lines, missing fields and odd
  values are skipped or read as zero, because log files are written by other
  programs while tokentally is reading them.
- Pricing is a flat dict of model prefix to `Price`. The longest prefix that
  ends at a separator wins.
- Grouping is a dict of key functions. Calendar keys are computed after
  converting the UTC timestamp into the report timezone.
