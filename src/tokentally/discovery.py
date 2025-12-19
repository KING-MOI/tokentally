"""Locate agent log files on disk."""

from __future__ import annotations

from pathlib import Path

PATTERNS: dict[str, str] = {
    "claude": "**/*.jsonl",
    "codex": "**/rollout-*.jsonl",
    "gemini": "*/chats/session-*.json",
}


def default_roots(source: str) -> list[Path]:
    home = Path.home()
    if source == "claude":
        return [home / ".claude" / "projects"]
    if source == "codex":
        return [home / ".codex" / "sessions"]
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
