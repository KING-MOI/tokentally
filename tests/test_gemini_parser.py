from pathlib import Path

from tokentally.parsers.gemini import parse_gemini_file

FIXTURE = (
    Path(__file__).parent
    / "fixtures"
    / "gemini"
    / "9e1d0c"
    / "chats"
    / "session-2026-03-03T08-00-4c2b.json"
)


def test_reads_gemini_messages_only() -> None:
    records = list(parse_gemini_file(FIXTURE))
    assert [r.model for r in records] == ["gemini-2.5-pro", "gemini-2.5-flash"]
    assert {r.session_id for r in records} == {"4c2b"}


def test_broken_file_yields_nothing(tmp_path: Path) -> None:
    f = tmp_path / "session-x.json"
    f.write_text("{not json", encoding="utf-8")
    assert list(parse_gemini_file(f)) == []


def test_token_split_matches_gemini_billing() -> None:
    pro = list(parse_gemini_file(FIXTURE))[0]
    assert pro.input_tokens == 5000
    assert pro.cache_read_tokens == 4000
    assert pro.output_tokens == 850


def test_project_is_the_gemini_project_hash() -> None:
    assert {r.project for r in parse_gemini_file(FIXTURE)} == {"9e1d0c"}


def test_messages_without_tokens_or_list_are_tolerated(tmp_path: Path) -> None:
    f = tmp_path / "session-y.json"
    f.write_text(
        '{"sessionId": "y", "messages": null}',
        encoding="utf-8",
    )
    assert list(parse_gemini_file(f)) == []
    f.write_text(
        '{"sessionId": "y", "messages": [{"type": "gemini", "timestamp": "2026-01-01T00:00:00Z"}]}',
        encoding="utf-8",
    )
    assert list(parse_gemini_file(f)) == []
