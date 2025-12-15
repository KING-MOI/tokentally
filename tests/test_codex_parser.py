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
