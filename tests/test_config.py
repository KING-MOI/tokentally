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


def test_price_overrides(tmp_path: Path) -> None:
    from tokentally.pricing import Price

    cfg = load_config(
        write(tmp_path, '[prices."My-Model"]\ninput = 1\noutput = 2.5\ncache_read = 0.1\n'),
    )
    assert cfg.prices == {"my-model": Price(input=1.0, output=2.5, cache_read=0.1)}


def test_price_with_unknown_field_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="prices.m"):
        load_config(write(tmp_path, "[prices.m]\ninput = 1\noutput = 1\nsurge = 9\n"))


def test_price_missing_output_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="prices.m"):
        load_config(write(tmp_path, "[prices.m]\ninput = 1\n"))


def test_unknown_source_in_paths_is_rejected(tmp_path: Path) -> None:
    with pytest.raises(ConfigError, match="cursor"):
        load_config(write(tmp_path, '[paths]\ncursor = "/x"\n'))


def test_template_is_valid_and_not_overwritten(tmp_path: Path) -> None:
    from tokentally.config import write_template

    p = tmp_path / "sub" / "config.toml"
    write_template(p)
    assert load_config(p).defaults == {}
    with pytest.raises(FileExistsError):
        write_template(p)


def test_budget(tmp_path: Path) -> None:
    cfg = load_config(write(tmp_path, "[budget]\ndaily = 20\nmonthly = 400.5\n"))
    assert cfg.budget == {"daily": 20.0, "monthly": 400.5}


@pytest.mark.parametrize(
    "text", ["[budget]\nweekly = 5\n", "[budget]\ndaily = -1\n", '[budget]\ndaily = "5"\n']
)
def test_bad_budget_is_rejected(tmp_path: Path, text: str) -> None:
    with pytest.raises(ConfigError, match="budget"):
        load_config(write(tmp_path, text))
