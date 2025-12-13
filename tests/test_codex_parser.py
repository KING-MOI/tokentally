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
