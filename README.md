# tokentally

[![ci](https://github.com/OWNER/tokentally/actions/workflows/ci.yml/badge.svg)](https://github.com/OWNER/tokentally/actions/workflows/ci.yml)
[![pypi](https://img.shields.io/pypi/v/tokentally.svg)](https://pypi.org/project/tokentally/)
[![python](https://img.shields.io/pypi/pyversions/tokentally.svg)](https://pypi.org/project/tokentally/)
[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Count the tokens your AI coding agents burn.

`tokentally` reads the session logs that Claude Code, Codex CLI and Gemini CLI
already write to your home directory, adds up the tokens per day, model,
session or project, and estimates what that usage would cost at API prices.
Nothing leaves your machine.

## Install

```sh
pip install tokentally
```

## Usage

```sh
tokentally              # daily report (same as `tokentally daily`)
tokentally models       # one row per model
tokentally monthly --since 2026-01-01
tokentally sessions --sort cost --limit 10
tokentally projects --source claude --format json
```

## Where logs are read from

| Agent | Default location | Override |
|---|---|---|
| Claude Code | `~/.claude/projects`, `~/.config/claude/projects` | `CLAUDE_CONFIG_DIR` (comma separated) |
| Codex CLI | `~/.codex/sessions` | `CODEX_HOME` |
| Gemini CLI | `~/.gemini/tmp/*/chats` | |

## Options

| Option | Meaning |
|---|---|
| `--since`, `--until` | Date range, inclusive. Accepts `2026-03-01`, `20260301`, `today`, `yesterday`, `7d`, `2w`. |
| `--source` | `claude`, `codex` or `gemini`. Repeat to pick several. |
| `--model`, `--project` | Case-insensitive substring filters. |
| `--tz` | IANA zone used for day boundaries. Defaults to local time. |
| `--sort` | `key` (default), `cost` or `tokens`. |
| `--limit N` | Show the first N rows. The total row still covers everything. |
| `--format` | `table` (default), `json` or `csv`. |

## About the cost numbers

Costs are estimates computed from per-model list prices for input, output,
cache writes and cache reads. They are what the same traffic would cost on the
pay-as-you-go API, which is not what a subscription plan bills. Models without a
known price are counted with zero cost and listed on stderr.

Claude Code can write prompt cache entries with a five minute or a one hour
TTL. One hour writes are billed at twice the input rate, so they are priced
separately from the default cache write rate.

## License

MIT, see [LICENSE](LICENSE).
