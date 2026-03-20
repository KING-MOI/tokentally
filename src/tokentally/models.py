"""Core data types."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class UsageRecord:
    """Token usage reported by one model response.

    ``cache_creation_1h_tokens`` is the part of ``cache_creation_tokens`` written
    with a one hour TTL, which Anthropic bills at a higher rate than the default
    five minute TTL.

    ``message_key`` identifies the API response the record came from, when the
    log provides one, so the same response seen in two files is counted once.
    """

    source: str
    timestamp: datetime
    model: str
    session_id: str
    project: str = ""
    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_tokens: int = 0
    cache_read_tokens: int = 0
    cache_creation_1h_tokens: int = 0
    message_key: str = ""

    @property
    def total_tokens(self) -> int:
        return (
            self.input_tokens
            + self.output_tokens
            + self.cache_creation_tokens
            + self.cache_read_tokens
        )
