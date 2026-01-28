# Changelog

## 0.3.0 - 2026-11-17

- Unpriced model warnings also appear for `summary`, `blocks` and `records`, once per run.
- Narrow terminals switch to the compact table layout automatically.
- Fast mode responses are priced at 2x, and Claude web searches at $10 per 1,000.
- `branches` report and `--breakdown branch` from Claude Code's git branch field.
## 0.2.0 - 2026-11-17

- Summary shows budget progress, busiest day, tokens per request and cache savings.
- Archived Codex sessions are read.
- Long context price tiers for Claude Sonnet 4/4.5 and Gemini Pro.
- `weekdays` and `hours` reports.
- `--output`, `--json`, `--share` and `--session` options.
- `records` command dumps matching records as JSON lines.
- Projects are keyed by full working directory, shown as `~/...` under home, so same-named folders no longer merge.
- Per-file parse cache; repeat runs skip unchanged logs. `--no-cache` bypasses it.
## 0.1.0 - 2026-11-17

- Parsers for Claude Code, Codex CLI and Gemini CLI logs.
- Daily, weekly, monthly, model, session, project and source reports.
- Date, source, model and project filters; timezone-aware day boundaries.
- Table, JSON and CSV output.
- `summary`, `blocks`, `pricing`, `paths` and `config` commands.
- `--breakdown`, `--compact`, `--chart`, `--svg` and `--svg-theme` options.
- TOML config file for defaults, log paths and price overrides.
- One hour cache writes are priced at twice the input rate.
- Responses copied into resumed Claude Code sessions are counted once.
- flaky test observed while testing
- follow up on the macOS build
- double-check error messages behavior
- double-check docs example behavior
- considered type narrowing; parked for now
- double-check exit codes behavior
- double-check the retry path behavior
- double-check the retry path behavior
- cache miss observed while testing
