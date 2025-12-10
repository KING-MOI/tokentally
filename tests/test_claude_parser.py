from pathlib import Path

from tokentally.parsers.claude import parse_claude_file

FIXTURE = Path(__file__).parent / "fixtures" / "claude" / "-home-dev-acme" / "0b1c-session.jsonl"


def test_parses_only_assistant_entries_with_usage() -> None:
    records = list(parse_claude_file(FIXTURE))
    assert len(records) == 3
    first = records[0]
    assert first.source == "claude"
    assert first.session_id == "0b1c"
    assert first.model == "claude-sonnet-4-5-20250929"
    assert (first.input_tokens, first.output_tokens) == (12, 340)
    assert (first.cache_creation_tokens, first.cache_read_tokens) == (2000, 0)
