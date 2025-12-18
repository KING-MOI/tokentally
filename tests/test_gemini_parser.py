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
