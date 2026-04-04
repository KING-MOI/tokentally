# Log formats

tokentally only reads files; it never talks to an API. This page records what
each agent writes and which fields are used, so parser behavior can be checked
against real logs.

## Claude Code

Location: `~/.claude/projects/<escaped-cwd>/<session-id>.jsonl`

One JSON object per line. Lines with `"type": "assistant"` carry a `message`
object with `model`, `id` and `usage`:

```json
{"type": "assistant", "sessionId": "…", "requestId": "req_…", "timestamp": "2026-03-01T09:00:05.000Z",
 "cwd": "/home/dev/acme",
 "message": {"id": "msg_…", "model": "claude-sonnet-4-5-20250929",
             "usage": {"input_tokens": 12, "output_tokens": 340,
                       "cache_creation_input_tokens": 2000, "cache_read_input_tokens": 0,
                       "cache_creation": {"ephemeral_5m_input_tokens": 2000, "ephemeral_1h_input_tokens": 0}}}}
```

Things to know:

- A single response is written as several lines, one per content block, each
  repeating the full `usage`. Lines are collapsed on `(message.id, requestId)`.
- Resumed and forked sessions copy earlier lines into the new file. The same
  key is used to count those only once across files.
- `"model": "<synthetic>"` lines and `isApiErrorMessage` lines are not API
  calls and are skipped.

## Codex CLI

Location: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`

Lines are `{"timestamp", "type", "payload"}`. Three types matter:

- `session_meta`: `payload.id` is the session id, `payload.cwd` the project.
- `turn_context`: `payload.model` is the model for the following turns.
- `event_msg` with `payload.type == "token_count"`: `payload.info` holds
  `last_token_usage` (this turn) and `total_token_usage` (running total).

`input_tokens` includes `cached_input_tokens`, so the cached part is moved into
the cache read bucket. Repeated events with an unchanged running total are
dropped. Logs from older versions that only have the running total are turned
into per-turn usage by subtracting consecutive totals.
