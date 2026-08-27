"""The full lineup. Adding a tool = write one module next to these and drop it
into ALL_PROVIDERS below. Everything downstream only touches UsageRecord, so
pricing, grouping and the dashboard all just work.
"""

from __future__ import annotations

import sys

from ..pricing.prices import cost_of
from ..types import PricedRecord
from . import claude, codex, cursor, gemini

# each entry: (name, label, collect_callable)
ALL_PROVIDERS = [
    (claude.NAME, claude.LABEL, claude.collect),
    (codex.NAME, codex.LABEL, codex.collect),
    (gemini.NAME, gemini.LABEL, gemini.collect),
    (cursor.NAME, cursor.LABEL, cursor.collect),
]

LABELS = {name: label for name, label, _ in ALL_PROVIDERS}


def label_for(name: str) -> str:
    return LABELS.get(name, name)


def collect_all(only: str | None = None) -> list[PricedRecord]:
    """Run every provider (or a chosen one), flatten to a single list, and attach
    a dollar cost to each. Providers that aren't installed just return [], so this
    quietly returns whatever you actually use.
    """
    providers = ALL_PROVIDERS
    if only:
        providers = [p for p in ALL_PROVIDERS if p[0] == only.lower()]

    priced: list[PricedRecord] = []
    for name, label, collect in providers:
        try:
            records = collect()
        except Exception as err:  # one broken tool shouldn't sink the whole report
            print(f"warning: couldn't read {label}: {err}", file=sys.stderr)
            continue
        for r in records:
            priced.append(
                PricedRecord(
                    provider=r.provider,
                    model=r.model,
                    project=r.project,
                    timestamp=r.timestamp,
                    activity=r.activity,
                    tokens=r.tokens,
                    id=r.id,
                    cost=cost_of(r.tokens, r.model),
                )
            )

    return priced
