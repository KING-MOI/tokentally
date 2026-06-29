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


def test_project_comes_from_cwd() -> None:
    assert {r.project for r in parse_claude_file(FIXTURE)} == {"/home/dev/acme"}


def test_one_hour_cache_writes_are_split_out(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text(
        '{"type":"assistant","timestamp":"2026-03-01T00:00:00Z","sessionId":"s",'
        '"message":{"id":"m","model":"claude-opus-5-5","usage":{"input_tokens":1,'
        '"output_tokens":1,"cache_creation_input_tokens":300,"cache_read_input_tokens":0,'
        '"cache_creation":{"ephemeral_5m_input_tokens":100,"ephemeral_1h_input_tokens":200}}}}\n',
        encoding="utf-8",
    )
    (rec,) = parse_claude_file(f)
    assert rec.cache_creation_tokens == 300
    assert rec.cache_creation_1h_tokens == 200


def test_api_error_placeholders_are_skipped(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text(
        '{"type":"assistant","isApiErrorMessage":true,"timestamp":"2026-03-01T00:00:00Z",'
        '"message":{"id":"e1","model":"claude-sonnet-4-5","usage":{"input_tokens":0,'
        '"output_tokens":0}}}\n',
        encoding="utf-8",
    )
    assert list(parse_claude_file(f)) == []


def test_same_folder_name_in_different_places_stays_separate(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    line = (
        '{{"type":"assistant","timestamp":"2026-03-01T00:00:00Z","cwd":"{cwd}",'
        '"message":{{"id":"{mid}","model":"m","usage":{{"output_tokens":1}}}}}}\n'
    )
    f.write_text(
        line.format(cwd="/work/app", mid="a") + line.format(cwd="/oss/app", mid="b"),
        encoding="utf-8",
    )
    assert [r.project for r in parse_claude_file(f)] == ["/work/app", "/oss/app"]


def test_git_branch_is_recorded() -> None:
    branches = [r.branch for r in parse_claude_file(FIXTURE)]
    assert branches == ["main", "", "fix/login"]


def test_fast_mode_responses_are_flagged(tmp_path: Path) -> None:
    f = tmp_path / "s.jsonl"
    f.write_text(
        '{"type":"assistant","timestamp":"2026-03-01T00:00:00Z","message":{"id":"a",'
        '"model":"claude-opus-5-5","usage":{"output_tokens":1,"speed":"fast"}}}\n'
        '{"type":"assistant","timestamp":"2026-03-01T00:00:01Z","message":{"id":"b",'
        '"model":"claude-opus-5-5","usage":{"output_tokens":1,"speed":"standard"}}}\n',
        encoding="utf-8",
    )
    assert [r.fast for r in parse_claude_file(f)] == [True, False]
