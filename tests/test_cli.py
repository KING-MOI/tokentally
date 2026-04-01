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
    monkeypatch.setenv("TOKENTALLY_CONFIG", str(tmp_path / "missing.toml"))
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
    assert "20250805" not in limited
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


def test_chart_flag_draws_bars(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["models", "--chart", "--metric", "tokens"]) == 0
    assert "█" in capsys.readouterr().out


def test_svg_option_writes_a_chart(fake_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "models.svg"
    assert main(["models", "--svg", str(out), "--format", "json"]) == 0
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<svg")
    assert "gpt-5-codex" in text


def test_svg_theme_option(fake_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "dark.svg"
    assert main(["sources", "--svg", str(out), "--svg-theme", "dark", "--format", "csv"]) == 0
    assert "#0d1117" in out.read_text(encoding="utf-8")


def test_time_reports_export_column_charts(fake_home: Path, tmp_path: Path) -> None:
    out = tmp_path / "daily.svg"
    assert main(["daily", "--svg", str(out), "--format", "csv"]) == 0
    assert "rotate(-45" in out.read_text(encoding="utf-8")


def write_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch, text: str) -> None:
    cfg = tmp_path / "tt.toml"
    cfg.write_text(text, encoding="utf-8")
    monkeypatch.setenv("TOKENTALLY_CONFIG", str(cfg))


def test_config_defaults_apply(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(fake_home, monkeypatch, '[defaults]\nsource = ["codex"]\nformat = "csv"\n')
    assert main(["models"]) == 0
    out = capsys.readouterr().out
    assert out.startswith("model,")
    assert "gpt-5-codex" in out and "claude" not in out


def test_command_line_beats_config(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(fake_home, monkeypatch, '[defaults]\nformat = "csv"\n')
    assert main(["models", "--format", "json"]) == 0
    assert capsys.readouterr().out.startswith("{")


def test_config_tz_is_converted(
    fake_home: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(fake_home, monkeypatch, '[defaults]\ntz = "Asia/Tokyo"\nsource = ["claude"]\n')
    assert main(["daily"]) == 0
    assert "2026-03-03" in capsys.readouterr().out


@pytest.mark.parametrize(
    "text",
    ['[defaults]\nsort = "vibes"\n', '[defaults]\ncolour = "red"\n', "[defaults\n"],
)
def test_bad_config_exits_with_code_2(
    fake_home: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    text: str,
) -> None:
    write_config(fake_home, monkeypatch, text)
    assert main(["models"]) == 2
    assert "config error" in capsys.readouterr().err


def test_config_paths_and_prices(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("COLUMNS", "200")
    write_config(
        tmp_path,
        monkeypatch,
        f'[paths]\ngemini = "{FIXTURES / "gemini"}"\n'
        '[prices."gemini-2.5-flash"]\ninput = 1000\noutput = 0\n',
    )
    assert main(["models", "--source", "gemini", "--format", "json"]) == 0
    import json

    rows = {r["model"]: r for r in json.loads(capsys.readouterr().out)["rows"]}
    assert rows["gemini-2.5-flash"]["cost"] == pytest.approx(1.2)


def test_config_init_path_and_show(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    target = tmp_path / "cfg" / "config.toml"
    monkeypatch.setenv("TOKENTALLY_CONFIG", str(target))
    assert main(["config", "show"]) == 1
    assert main(["config", "path"]) == 0
    assert capsys.readouterr().out.strip() == str(target)
    assert main(["config", "init"]) == 0
    assert target.exists()
    assert main(["config", "init"]) == 1
    capsys.readouterr()
    assert main(["config", "show"]) == 0
    assert "[defaults]" in capsys.readouterr().out


def test_config_path_works_when_the_config_is_broken(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    write_config(tmp_path, monkeypatch, "[defaults\n")
    assert main(["config", "path"]) == 0
    assert main(["config", "show"]) == 0
    assert "[defaults" in capsys.readouterr().out


def test_unknown_models_are_flagged_on_stderr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    proj = tmp_path / ".claude" / "projects" / "p"
    proj.mkdir(parents=True)
    (proj / "s.jsonl").write_text(
        '{"type":"assistant","timestamp":"2026-03-01T00:00:00Z","sessionId":"s",'
        '"message":{"id":"m","model":"claude-nova-9","usage":{"output_tokens":5}}}\n',
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    monkeypatch.setenv("TOKENTALLY_CONFIG", str(tmp_path / "none.toml"))
    assert main(["models", "--source", "claude", "--format", "csv"]) == 0
    assert "no price for claude-nova-9" in capsys.readouterr().err


def test_pricing_command_filters_models(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    assert main(["pricing", "haiku"]) == 0
    out = capsys.readouterr().out
    assert "claude-haiku-4-5" in out
    assert "sonnet" not in out


def test_hourly_report(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["hourly", "--source", "codex", "--tz", "UTC"]) == 0
    assert "2026-03-01 10:00" in capsys.readouterr().out


def test_summary_command(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["summary", "--tz", "UTC", "--format", "json"]) == 0
    doc = json.loads(capsys.readouterr().out)
    assert doc["first_day"] == "2026-03-01"
    assert doc["last_day"] == "2026-03-03"
    assert len(doc["daily_cost"]) == 3
    assert main(["summary"]) == 0
    assert "Cache hit rate" in capsys.readouterr().out


def test_blocks_command(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["blocks", "--tz", "UTC"]) == 0
    out = capsys.readouterr().out
    assert "2026-03-01 09:00" in out
    assert main(["blocks", "--active"]) == 0
    assert "no active block" in capsys.readouterr().out


def test_bad_date_has_a_helpful_message(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    with pytest.raises(SystemExit):
        main(["daily", "--since", "last week"])
    assert "invalid date 'last week'" in capsys.readouterr().err


@pytest.mark.parametrize("value", ["0", "-3", "ten"])
def test_limit_must_be_positive(fake_home: Path, value: str) -> None:
    with pytest.raises(SystemExit) as exc:
        main(["models", "--limit", value])
    assert exc.value.code == 2


def test_since_after_until_is_an_error(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["daily", "--since", "2026-03-05", "--until", "2026-03-01"]) == 2
    assert "is after --until" in capsys.readouterr().err


def test_unwritable_svg_path_is_a_clean_error(
    fake_home: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    target = fake_home / "missing-dir" / "out.svg"
    assert main(["models", "--svg", str(target)]) == 1
    assert "cannot write" in capsys.readouterr().err


def test_empty_selection_says_so(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["daily", "--model", "nothing-matches"]) == 0
    assert "no usage found" in capsys.readouterr().out


def test_breakdown_option(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["daily", "--tz", "UTC", "--breakdown", "source"]) == 0
    out = capsys.readouterr().out
    assert "└ gemini" in out


def test_breakdown_in_json(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["sources", "--breakdown", "model", "--format", "json"]) == 0
    rows = {r["source"]: r for r in json.loads(capsys.readouterr().out)["rows"]}
    assert [b["model"] for b in rows["gemini"]["breakdown"]] == [
        "gemini-2.5-flash",
        "gemini-2.5-pro",
    ]


def test_breakdown_rows_follow_sort(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    import json

    assert main(["sources", "--breakdown", "model", "--sort", "cost", "--format", "json"]) == 0
    rows = {r["source"]: r for r in json.loads(capsys.readouterr().out)["rows"]}
    assert rows["gemini"]["breakdown"][0]["model"] == "gemini-2.5-pro"


def test_compact_flag(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["models", "--compact"]) == 0
    assert "Cache read" not in capsys.readouterr().out


def test_paths_command(fake_home: Path, capsys: pytest.CaptureFixture[str]) -> None:
    assert main(["paths"]) == 0
    out = capsys.readouterr().out
    assert "missing" in out
    assert ".codex" in out
