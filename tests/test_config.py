from pathlib import Path

import pytest

from tokentally.config import ConfigError, config_path, load_config


def write(tmp_path: Path, text: str) -> Path:
    p = tmp_path / "config.toml"
    p.write_text(text, encoding="utf-8")
    return p


def test_missing_file_is_an_empty_config(tmp_path: Path) -> None:
    assert load_config(tmp_path / "nope.toml").defaults == {}


def test_reads_defaults_table(tmp_path: Path) -> None:
    cfg = load_config(write(tmp_path, '[defaults]\ntz = "UTC"\nsort = "cost"\n'))
    assert cfg.defaults == {"tz": "UTC", "sort": "cost"}


def test_invalid_toml_names_the_file(tmp_path: Path) -> None:
    p = write(tmp_path, "[defaults\n")
    with pytest.raises(ConfigError, match="config.toml"):
        load_config(p)


def test_config_path_precedence(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("TOKENTALLY_CONFIG", "/etc/tt.toml")
    assert config_path() == Path("/etc/tt.toml")
    monkeypatch.delenv("TOKENTALLY_CONFIG")
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert config_path() == tmp_path / "tokentally" / "config.toml"


def test_paths_accept_a_string_or_a_list(tmp_path: Path) -> None:
    cfg = load_config(
        write(tmp_path, '[paths]\nclaude = "~/c"\ncodex = ["/a", "/b"]\n'),
    )
    assert cfg.paths["claude"] == [Path("~/c").expanduser()]
    assert cfg.paths["codex"] == [Path("/a"), Path("/b")]


def test_bad_paths_entry_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="paths.claude"):
        load_config(write(tmp_path, "[paths]\nclaude = 3\n"))
