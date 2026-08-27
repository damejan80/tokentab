"""Shared number formatting so the CLI and JSON output agree."""

from __future__ import annotations


def money(n: float) -> str:
    if n >= 1000:
        return "$" + f"{round(n):,}"
    if n >= 1:
        return "$" + f"{n:.2f}"
    if n == 0:
        return "$0.00"
    return "$" + f"{n:.3f}"


def compact_tokens(n: int) -> str:
    if n >= 1e9:
        return f"{n / 1e9:.2f}B"
    if n >= 1e6:
        return f"{n / 1e6:.1f}M"
    if n >= 1e3:
        return f"{n / 1e3:.1f}K"
    return str(n)


def pct(x: float) -> str:
    return f"{x * 100:.1f}%"


def share(cost: float, total: float) -> str:
    if total <= 0:
        return "0%"
    return f"{round(cost / total * 100)}%"
