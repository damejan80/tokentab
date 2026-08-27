"""Model prices, in US dollars per 1 MILLION tokens.

I keep these by hand instead of hitting a pricing API, because (a) I don't want
the tool phoning home just to add up numbers, and (b) a wrong-but-close number
beats a crash when a vendor renames a model overnight. If a price here drifts,
it's a one-line change.

Sources: each vendor's public pricing page. Last eyeballed: mid-2026.
If you spot a stale number, please open an issue — I'd rather be corrected.
"""

from __future__ import annotations

from ..types import ModelPrice, TokenCounts

TABLE: dict[str, ModelPrice] = {
    # --- Anthropic (Claude) ---
    "claude-opus-4-6":   ModelPrice(15, 75, 1.5, 18.75),
    "claude-opus-4-5":   ModelPrice(15, 75, 1.5, 18.75),
    "claude-opus-4-1":   ModelPrice(15, 75, 1.5, 18.75),
    "claude-opus-4":     ModelPrice(15, 75, 1.5, 18.75),
    "claude-sonnet-4-6": ModelPrice(3, 15, 0.3, 3.75),
    "claude-sonnet-4-5": ModelPrice(3, 15, 0.3, 3.75),
    "claude-sonnet-4":   ModelPrice(3, 15, 0.3, 3.75),
    "claude-haiku-4-5":  ModelPrice(1, 5, 0.1, 1.25),
    "claude-3-5-haiku":  ModelPrice(0.8, 4, 0.08, 1),

    # --- OpenAI (Codex / GPT) ---
    "gpt-5.6":      ModelPrice(1.25, 10, 0.125, 0),
    "gpt-5.1":      ModelPrice(1.25, 10, 0.125, 0),
    "gpt-5":        ModelPrice(1.25, 10, 0.125, 0),
    "gpt-5-mini":   ModelPrice(0.25, 2, 0.025, 0),
    "gpt-5-codex":  ModelPrice(1.25, 10, 0.125, 0),
    "gpt-4o":       ModelPrice(2.5, 10, 1.25, 0),
    "gpt-4o-mini":  ModelPrice(0.15, 0.6, 0.075, 0),
    "o3":           ModelPrice(2, 8, 0.5, 0),
    "o4-mini":      ModelPrice(1.1, 4.4, 0.275, 0),

    # --- Google (Gemini) ---
    "gemini-3.5-pro":   ModelPrice(2.5, 15, 0.25, 0),
    "gemini-3.5-flash": ModelPrice(0.3, 2.5, 0.03, 0),
    "gemini-2.5-pro":   ModelPrice(1.25, 10, 0.125, 0),
    "gemini-2.5-flash": ModelPrice(0.3, 2.5, 0.03, 0),
}

# When a log says "claude-opus-4-6-20260514" or "anthropic/claude-sonnet-4-6" we
# won't find an exact key, so we try progressively looser matches. Longest keys
# first, so "claude-opus-4-6" wins over "claude-opus-4".
_KEYS_BY_LENGTH = sorted(TABLE.keys(), key=len, reverse=True)

_unknown_models: set[str] = set()


def price_for(model: str) -> ModelPrice | None:
    if not model:
        return None
    m = model.lower()

    if m in TABLE:
        return TABLE[m]

    # strip a leading vendor prefix like "anthropic/" or "openai/"
    bare = m.split("/")[-1] if "/" in m else m
    if bare in TABLE:
        return TABLE[bare]

    # substring match — handles date-stamped and suffixed names
    for key in _KEYS_BY_LENGTH:
        if key in bare:
            return TABLE[key]

    _unknown_models.add(model)
    return None


def unpriced_models() -> list[str]:
    """Models we saw but couldn't price. The CLI warns so $0 rows aren't a silent lie."""
    return sorted(_unknown_models)


def cost_of(tokens: TokenCounts, model: str) -> float:
    """Cost in dollars for one set of token counts on a given model."""
    p = price_for(model)
    if p is None:
        return 0.0
    return (
        tokens.input * p.input
        + tokens.output * p.output
        + tokens.cache_read * p.cache_read
        + tokens.cache_write * p.cache_write
    ) / 1_000_000
