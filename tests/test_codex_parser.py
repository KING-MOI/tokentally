from pathlib import Path

from tokentally.parsers.codex import parse_codex_file

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "codex"
    / "2026"
    / "03"
    / "01"
    / "rollout-2026-03-01T10-00-00-7f3a.jsonl"
)


def test_reads_model_and_session_from_context_events() -> None:
    records = list(parse_codex_file(FIXTURE))
    assert records
    assert {r.model for r in records} == {"gpt-5-codex"}
    assert {r.session_id for r in records} == {"7f3a"}
    assert {r.source for r in records} == {"codex"}


def test_cached_tokens_are_not_double_counted_as_input() -> None:
    records = list(parse_codex_file(FIXTURE))
    assert sum(r.cache_read_tokens for r in records) == 8000
    assert sum(r.input_tokens for r in records) == 3000


def test_repeated_token_count_event_is_ignored() -> None:
    records = list(parse_codex_file(FIXTURE))
    assert len(records) == 2
    assert sum(r.output_tokens for r in records) == 700


def test_project_comes_from_session_cwd() -> None:
    assert {r.project for r in parse_codex_file(FIXTURE)} == {"widgets"}


def test_older_logs_with_only_running_totals_use_deltas(tmp_path: Path) -> None:
    f = tmp_path / "rollout-old.jsonl"
    lines = [
        '{"timestamp":"2026-01-01T00:00:00Z","type":"turn_context","payload":{"model":"gpt-5"}}',
        '{"timestamp":"2026-01-01T00:00:01Z","type":"event_msg","payload":{"type":"token_count",'
        '"info":{"total_token_usage":{"input_tokens":100,"cached_input_tokens":0,"output_tokens":10}}}}',
        '{"timestamp":"2026-01-01T00:00:02Z","type":"event_msg","payload":{"type":"token_count",'
        '"info":{"total_token_usage":{"input_tokens":250,"cached_input_tokens":90,"output_tokens":30}}}}',
    ]
    f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    records = list(parse_codex_file(f))
    assert [(r.input_tokens, r.cache_read_tokens, r.output_tokens) for r in records] == [
        (100, 0, 10),
        (60, 90, 20),
    ]


def test_project_falls_back_to_turn_context_cwd(tmp_path: Path) -> None:
    f = tmp_path / "rollout-x.jsonl"
    f.write_text(
        '{"timestamp":"2026-01-01T00:00:00Z","type":"turn_context",'
        '"payload":{"model":"gpt-5","cwd":"/src/gadget"}}\n'
        '{"timestamp":"2026-01-01T00:00:01Z","type":"event_msg","payload":{"type":"token_count",'
        '"info":{"last_token_usage":{"input_tokens":1,"output_tokens":1}}}}\n',
        encoding="utf-8",
    )
    assert [r.project for r in parse_codex_file(f)] == ["gadget"]
