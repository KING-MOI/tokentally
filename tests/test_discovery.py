from pathlib import Path

import pytest

from tokentally.discovery import default_roots, find_logs

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("source", ["claude", "codex", "gemini"])
def test_finds_fixture_logs(source: str) -> None:
    files = find_logs(source, [FIXTURES / source])
    assert len(files) == 1


def test_missing_root_is_ignored(tmp_path: Path) -> None:
    assert find_logs("claude", [tmp_path / "nope"]) == []


def test_default_roots_live_under_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    assert default_roots("codex") == [tmp_path / ".codex" / "sessions"]


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(ValueError):
        default_roots("cursor")
