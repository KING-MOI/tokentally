"""Locate agent log files on disk."""

from __future__ import annotations

import os
from pathlib import Path

PATTERNS: dict[str, str] = {
    "claude": "**/*.jsonl",
    "codex": "**/rollout-*.jsonl",
    "gemini": "*/chats/session-*.json",
}


def default_roots(source: str) -> list[Path]:
    home = Path.home()
    if source == "claude":
        env = os.environ.get("CLAUDE_CONFIG_DIR")
        if env:
            return [Path(p).expanduser() / "projects" for p in env.split(",") if p.strip()]
        return [home / ".claude" / "projects", home / ".config" / "claude" / "projects"]
    if source == "codex":
        codex_home = os.environ.get("CODEX_HOME")
        base = Path(codex_home).expanduser() if codex_home else home / ".codex"
        return [base / "sessions"]
    if source == "gemini":
        return [home / ".gemini" / "tmp"]
    raise ValueError(f"unknown source: {source}")


def find_logs(source: str, roots: list[Path] | None = None) -> list[Path]:
    """Return every log file for ``source`` under ``roots``, sorted."""
    pattern = PATTERNS[source]
    found: set[Path] = set()
    for root in roots if roots is not None else default_roots(source):
        if root.is_dir():
            found.update(p for p in root.glob(pattern) if p.is_file())
    return sorted(found)
