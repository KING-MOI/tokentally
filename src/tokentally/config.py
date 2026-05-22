"""User configuration loaded from a TOML file."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from tokentally.parsers import PARSERS
from tokentally.pricing import Price


class ConfigError(Exception):
    """Raised when the config file exists but cannot be used."""


@dataclass(slots=True)
class Config:
    defaults: dict[str, Any] = field(default_factory=dict)
    paths: dict[str, list[Path]] = field(default_factory=dict)
    prices: dict[str, Price] = field(default_factory=dict)
    budget: dict[str, float] = field(default_factory=dict)


def config_path() -> Path:
    """Location of the config file, honoring TOKENTALLY_CONFIG and XDG_CONFIG_HOME."""
    explicit = os.environ.get("TOKENTALLY_CONFIG")
    if explicit:
        return Path(explicit).expanduser()
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    return base / "tokentally" / "config.toml"


def load_config(path: Path | None = None) -> Config:
    """Read the config file; a missing file means an empty config."""
    path = path or config_path()
    try:
        raw = tomllib.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return Config()
    except tomllib.TOMLDecodeError as exc:
        raise ConfigError(f"{path}: {exc}") from exc
    defaults = raw.get("defaults", {})
    if not isinstance(defaults, dict):
        raise ConfigError(f"{path}: [defaults] must be a table")
    paths: dict[str, list[Path]] = {}
    for source, value in raw.get("paths", {}).items():
        if source not in PARSERS:
            raise ConfigError(f"{path}: unknown source in [paths]: {source}")
        entries = [value] if isinstance(value, str) else value
        if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
            raise ConfigError(f"{path}: paths.{source} must be a path or list of paths")
        paths[source] = [Path(e).expanduser() for e in entries]
    prices: dict[str, Price] = {}
    for model, spec in raw.get("prices", {}).items():
        if not isinstance(spec, dict):
            raise ConfigError(f"{path}: prices.{model} must be a table")
        try:
            prices[model.lower()] = Price(**{k: float(v) for k, v in spec.items()})
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"{path}: prices.{model}: {exc}") from exc
    budget: dict[str, float] = {}
    for period, amount in raw.get("budget", {}).items():
        if period not in ("daily", "monthly"):
            raise ConfigError(f"{path}: unknown budget period: {period}")
        if isinstance(amount, bool) or not isinstance(amount, int | float) or amount <= 0:
            raise ConfigError(f"{path}: budget.{period} must be a positive number")
        budget[period] = float(amount)
    return Config(defaults=defaults, paths=paths, prices=prices, budget=budget)


TEMPLATE = """\
# tokentally configuration

[defaults]
# tz = "America/Los_Angeles"
# source = ["claude", "codex", "gemini"]
# sort = "cost"
# svg_theme = "dark"

[paths]
# claude = ["~/.claude/projects"]
# codex = "~/.codex/sessions"
# gemini = "~/.gemini/tmp"

# Spending limits in USD, shown by `tokentally summary`.
[budget]
# daily = 20
# monthly = 400

# Prices are USD per million tokens.
# [prices."my-finetune"]
# input = 3.0
# output = 15.0
# cache_write = 3.75
# cache_read = 0.30
"""


def write_template(path: Path) -> None:
    """Create a commented starter config; refuses to overwrite."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8") as fh:
        fh.write(TEMPLATE)
