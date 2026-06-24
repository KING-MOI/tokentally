# Commands

| Command | Rows |
|---|---|
| `hourly`, `daily`, `weekly`, `monthly` | One per calendar bucket in the chosen timezone |
| `models` | One per model; dated snapshots merge into their base name |
| `sessions` | One per agent session |
| `projects` | One per project (working directory name) |
| `sources` | One per agent CLI |
| `branches` | One per git branch (Claude Code only) |
| `weekdays` | One per day of the week, Monday first |
| `hours` | One per hour of the day, to see when you work |
| `summary` | Headline numbers and a daily cost sparkline |
| `blocks` | Five hour billing windows, with a projection for the running one |
| `records` | Every matching record as one JSON line, for your own analysis |
| `pricing` | The price table in use, including config overrides |
| `paths` | Where logs are searched for and how many files were found |
| `config` | `path`, `init` or `show` the config file |

Running `tokentally` with no command is the same as `tokentally daily`.

## Report options

All row reports (`hourly` through `sources`) accept:

- `--sort key|cost|tokens` and `--limit N`
- `--share` to add each row's share of the total cost
- `--breakdown model|project|source|branch` to add indented sub-rows
- `--compact` to drop the cache columns
- `--format table|json|csv` (or `--json`), and `-o FILE` to write json or csv to a file
- `--chart` and `--metric cost|tokens` for a bar chart under the table
- `--svg FILE` and `--svg-theme light|dark` to save the chart

`summary`, `blocks` and `records` accept only the selection options:
`--since`, `--until`, `--source`, `--model`, `--project`, `--session`, `--tz`
and `--no-cache`.

## `blocks`

Claude subscription limits are tracked in five hour windows. A window opens on
the hour of the first request after the previous one closed. `blocks` shows one
row per window; the running window shows the time left and the cost it would
reach at the current burn rate.

```sh
tokentally blocks --since today
tokentally blocks --active --watch 30
```
