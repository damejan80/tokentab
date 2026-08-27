"""The shapes the whole app speaks in.

Every provider parser turns its own weird log format into a list of UsageRecord,
and everything downstream — pricing, grouping, the dashboard — only ever touches
that. Adding a new tool means writing one parser that yields UsageRecords and
nothing else changes.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class TokenCounts:
    input: int = 0
    output: int = 0
    cache_read: int = 0   # tokens read back from the prompt cache (cheap)
    cache_write: int = 0  # tokens written into the cache (a bit pricier than input)

    def total(self) -> int:
        return self.input + self.output + self.cache_read + self.cache_write


@dataclass
class UsageRecord:
    provider: str          # "claude", "codex", "gemini", "cursor"
    model: str             # model name as the tool reported it
    project: str           # project / working directory (best effort)
    timestamp: datetime    # when the call happened
    activity: str          # rough guess at what the turn was doing
    tokens: TokenCounts
    id: str                # stable-ish id so we can drop duplicates


@dataclass
class PricedRecord(UsageRecord):
    cost: float = 0.0


@dataclass
class ModelPrice:
    """A model's price, in US dollars per 1 million tokens."""
    input: float
    output: float
    cache_read: float
    cache_write: float
