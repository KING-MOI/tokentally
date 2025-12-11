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


def test_synthetic_messages_are_ignored() -> None:
    assert all(r.model != "<synthetic>" for r in parse_claude_file(FIXTURE))


def test_message_split_across_lines_is_counted_once() -> None:
    records = list(parse_claude_file(FIXTURE))
    assert sum(r.output_tokens for r in records if r.model.startswith("claude-opus")) == 900


def test_entries_without_a_usable_timestamp_are_skipped(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text(
        '{"type":"assistant","message":{"model":"m","usage":{"output_tokens":1}}}\n'
        '{"type":"assistant","timestamp":"yesterday","message":{"model":"m","usage":{"output_tokens":1}}}\n',
        encoding="utf-8",
    )
    assert list(parse_claude_file(f)) == []
