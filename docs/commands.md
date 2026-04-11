# Commands

| Command | Rows |
|---|---|
| `hourly`, `daily`, `weekly`, `monthly` | One per calendar bucket in the chosen timezone |
| `models` | One per model; dated snapshots merge into their base name |
| `sessions` | One per agent session |
| `projects` | One per project (working directory name) |
| `sources` | One per agent CLI |
| `summary` | Headline numbers and a daily cost sparkline |
| `blocks` | Five hour billing windows, with a projection for the running one |
| `pricing` | The price table in use, including config overrides |
| `paths` | Where logs are searched for and how many files were found |
| `config` | `path`, `init` or `show` the config file |

Running `tokentally` with no command is the same as `tokentally daily`.
