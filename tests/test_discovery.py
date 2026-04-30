from pathlib import Path

import pytest

from tokentally.discovery import default_roots, find_logs

from conftest import set_home

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.mark.parametrize("source", ["claude", "codex", "gemini"])
def test_finds_fixture_logs(source: str) -> None:
    files = find_logs(source, [FIXTURES / source])
    assert len(files) == (2 if source == "claude" else 1)


def test_missing_root_is_ignored(tmp_path: Path) -> None:
    assert find_logs("claude", [tmp_path / "nope"]) == []


def test_default_roots_live_under_home(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CODEX_HOME", raising=False)
    set_home(monkeypatch, tmp_path)
    assert default_roots("codex") == [tmp_path / ".codex" / "sessions"]


def test_unknown_source_is_rejected() -> None:
    with pytest.raises(ValueError):
        default_roots("cursor")


def test_claude_config_dir_env_overrides_home(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CLAUDE_CONFIG_DIR", "/a,/b")
    assert default_roots("claude") == [Path("/a/projects"), Path("/b/projects")]


def test_claude_checks_xdg_location_too(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("CLAUDE_CONFIG_DIR", raising=False)
    set_home(monkeypatch, tmp_path)
    assert tmp_path / ".config" / "claude" / "projects" in default_roots("claude")


def test_codex_home_env_is_respected(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CODEX_HOME", "/opt/codex")
    assert default_roots("codex") == [Path("/opt/codex/sessions")]


def test_load_records_merges_sources_in_time_order() -> None:
    from tokentally.discovery import load_records

    roots = {s: [FIXTURES / s] for s in ("claude", "codex", "gemini")}
    records = load_records(roots, roots)
    assert {r.source for r in records} == {"claude", "codex", "gemini"}
    assert [r.timestamp for r in records] == sorted(r.timestamp for r in records)


def test_resumed_session_does_not_double_count_copied_history() -> None:
    from tokentally.discovery import load_records

    records = load_records(["claude"], {"claude": [FIXTURES / "claude"]})
    keys = [r.message_key for r in records]
    assert keys.count("msg_2:req_2") == 1
    assert "msg_9:req_9" in keys


def test_describe_roots_counts_files_and_flags_missing(tmp_path: Path) -> None:
    from tokentally.discovery import describe_roots

    rows = describe_roots(
        ["claude", "codex"],
        {"claude": [FIXTURES / "claude", tmp_path / "gone"], "codex": [FIXTURES / "codex"]},
    )
    assert rows == [
        ("claude", FIXTURES / "claude", 2),
        ("claude", tmp_path / "gone", None),
        ("codex", FIXTURES / "codex", 1),
    ]


def test_cached_files_are_not_parsed_again(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    import tokentally.discovery as discovery
    from tokentally.cache import FileCache

    roots = {"codex": [FIXTURES / "codex"]}
    cache = FileCache(tmp_path / "records.json")
    first = discovery.load_records(["codex"], roots, cache)
    monkeypatch.setitem(discovery.PARSERS, "codex", lambda p: iter(()))
    assert discovery.load_records(["codex"], roots, cache) == first
    assert discovery.load_records(["codex"], roots) == []
