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


def test_models_report_lists_every_model(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
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


def test_since_and_until_narrow_the_report(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["daily", "--since", "2026-03-03", "--until", "2026-03-03", "--tz", "UTC"]) == 0
    out = capsys.readouterr().out
    assert "2026-03-03" in out
    assert "2026-03-01" not in out


def test_source_option_limits_logs_read(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["models", "--source", "codex"]) == 0
    out = capsys.readouterr().out
    assert "gpt-5-codex" in out
    assert "claude" not in out


def test_model_filter(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["models", "--model", "opus"]) == 0
    out = capsys.readouterr().out
    assert "claude-opus-4-1" in out
    assert "sonnet" not in out


def test_tz_moves_day_boundaries(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["daily", "--source", "claude", "--tz", "UTC"]) == 0
    utc = capsys.readouterr().out
    assert main(["daily", "--source", "claude", "--tz", "Asia/Tokyo"]) == 0
    tokyo = capsys.readouterr().out
    assert "2026-03-03" not in utc
    assert "2026-03-03" in tokyo


def test_unknown_timezone_is_a_usage_error(fake_home: Path) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["daily", "--tz", "Mars/Olympus"])
    assert exc.value.code == 2


def test_options_work_without_a_subcommand(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["--source", "gemini", "--tz", "UTC"]) == 0
    out = capsys.readouterr().out
    assert "2026-03-03" in out
    assert "2026-03-01" not in out


def test_sort_by_cost_puts_most_expensive_first(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["models", "--source", "claude", "--sort", "cost"]) == 0
    out = capsys.readouterr().out
    assert out.index("claude-opus-4-1") < out.index("claude-sonnet-4-5")


def test_limit_keeps_first_rows_but_total_covers_everything(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["models", "--sort", "cost", "--limit", "1"]) == 0
    limited = capsys.readouterr().out
    assert main(["models"]) == 0
    full = capsys.readouterr().out
    assert "claude-opus-4-1" in limited
    assert "gemini" not in limited

    def footer(text: str) -> list[str]:
        return text.strip().splitlines()[-2].split()

    assert footer(limited) == footer(full)


def test_json_format(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["sources", "--format", "json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert [row["source"] for row in doc["rows"]] == ["claude", "codex", "gemini"]


def test_csv_format(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["sources", "--format", "csv"]) == 0
    assert capsys.readouterr().out.splitlines()[0].startswith("source,")
