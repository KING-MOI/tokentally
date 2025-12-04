"""Core data types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UsageRecord:
    """Token usage reported by one model response."""

    source: str
    timestamp: datetime
    model: str
    session_id: str
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
