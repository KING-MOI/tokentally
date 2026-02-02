from pathlib import Path

import pytest

from tokentally.cli import main

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fake_home(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("COLUMNS", "200")
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.delenv("CODEX_HOME", raising=False)
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "projects").symlink_to(FIXTURES / "claude")
    (tmp_path / ".codex").mkdir()
    (tmp_path / ".codex" / "sessions").symlink_to(FIXTURES / "codex")
    (tmp_path / ".gemini").mkdir()
    (tmp_path / ".gemini" / "tmp").symlink_to(FIXTURES / "gemini")
    return tmp_path


def test_models_report_lists_every_model(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["models"]) == 0
    out = capsys.readouterr().out
    for model in ("claude-sonnet-4-5", "gpt-5-codex", "gemini-2.5-pro"):
        assert model in out


def test_daily_is_the_default_report(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main([]) == 0
    assert "Date" in capsys.readouterr().out


def test_monthly_report(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["monthly"]) == 0
    assert "2026-03" in capsys.readouterr().out


def test_projects_report(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["projects"]) == 0
    out = capsys.readouterr().out
    assert "acme" in out and "widgets" in out


def test_since_and_until_narrow_the_report(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["daily", "--since", "2026-03-03", "--until", "2026-03-03"]) == 0
    out = capsys.readouterr().out
    assert "2026-03-03" in out
    assert "2026-03-01" not in out
