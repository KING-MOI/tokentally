"""User configuration loaded from a TOML file."""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(Exception):
    """Raised when the config file exists but cannot be used."""


@dataclass(slots=True)
class Config:
    defaults: dict[str, Any] = field(default_factory=dict)
    paths: dict[str, list[Path]] = field(default_factory=dict)


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
        entries = [value] if isinstance(value, str) else value
        if not isinstance(entries, list) or not all(isinstance(e, str) for e in entries):
            raise ConfigError(f"{path}: paths.{source} must be a path or list of paths")
        paths[source] = [Path(e).expanduser() for e in entries]
    return Config(defaults=defaults, paths=paths)
