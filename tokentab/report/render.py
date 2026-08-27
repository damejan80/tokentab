"""Draw the report in the terminal with rich."""

from __future__ import annotations

from datetime import datetime, timezone

from rich.box import SIMPLE_HEAVY
from rich.console import Console, Group
from rich.table import Table
from rich.text import Text

from ..providers import label_for
from .aggregate import Report
from .format import compact_tokens, money, pct, share


def _fmt_day(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def _bar(value: float, mx: float, width: int = 24) -> Text:
    if mx <= 0:
        return Text("")
    filled = round(value / mx * width)
    t = Text("▇" * filled, style="yellow")
    t.append("░" * max(0, width - filled), style="grey37")
    return t


def render_report(report: Report, console: Console) -> None:
    totals = report.totals

    if report.range.frm.timestamp() == 0:
        range_label = "all time"
    else:
        range_label = f"{_fmt_day(report.range.frm)} → {_fmt_day(report.range.to)}"

    console.print()
    console.print(Text("  tokentab  ", style="bold white") + Text(range_label, style="grey58"))
    console.print()

    # ---- headline totals ----
    console.print(Text("Totals", style="bold"))
    parts = Text("  ")
    parts.append("cost ", style="grey58")
    parts.append(money(totals.cost) + "   ·   ", style="green")
    parts.append("tokens ", style="grey58")
    parts.append(compact_tokens(totals.tokens.total()) + "   ·   ")
    parts.append("calls ", style="grey58")
    parts.append(f"{totals.calls:,}" + "   ·   ")
    parts.append("cache hit ", style="grey58")
    parts.append(pct(totals.cache_hit_rate))
    console.print(parts)
    console.print()

    if totals.calls == 0:
        console.print(Text("  No usage found for this window.", style="yellow"))
        console.print(
            Text(
                "  Either nothing ran in this period, or none of the supported tools have logs on disk yet.",
                style="grey58",
            )
        )
        console.print()
        return

    # ---- by tool ----
    console.print(Text("By tool", style="bold"))
    t = Table(box=SIMPLE_HEAVY, show_edge=True, pad_edge=False)
    t.add_column("Tool")
    t.add_column("Cost", justify="right", style="green")
    t.add_column("Tokens", justify="right")
    t.add_column("Share", justify="right")
    for r in report.by_tool:
        t.add_row(label_for(r.label), money(r.cost), compact_tokens(r.tokens), share(r.cost, totals.cost))
    console.print(t)

    # ---- top models ----
    console.print(Text("Top models", style="bold"))
    t = Table(box=SIMPLE_HEAVY, pad_edge=False)
    t.add_column("Model")
    t.add_column("Cost", justify="right", style="green")
    t.add_column("Tokens", justify="right")
    t.add_column("Calls", justify="right")
    for r in report.by_model[:8]:
        t.add_row(r.label, money(r.cost), compact_tokens(r.tokens), str(r.calls))
    console.print(t)

    # ---- top projects ----
    if len(report.by_project) > 1:
        console.print(Text("Top projects", style="bold"))
        t = Table(box=SIMPLE_HEAVY, pad_edge=False)
        t.add_column("Project")
        t.add_column("Cost", justify="right", style="green")
        t.add_column("Tokens", justify="right")
        for r in report.by_project[:8]:
            t.add_row(r.label, money(r.cost), compact_tokens(r.tokens))
        console.print(t)

    # ---- by activity ----
    console.print(Text("By activity", style="bold"))
    t = Table(box=SIMPLE_HEAVY, pad_edge=False)
    t.add_column("Activity")
    t.add_column("Cost", justify="right", style="green")
    t.add_column("Share", justify="right")
    for r in report.by_activity:
        t.add_row(r.label, money(r.cost), share(r.cost, totals.cost))
    console.print(t)

    # ---- per day ----
    if len(report.by_day) > 1:
        console.print(Text("Per day", style="bold"))
        max_cost = max((d.cost for d in report.by_day), default=0.0)
        for d in report.by_day[-14:]:
            line = Text("  ")
            line.append(d.date + "  ", style="grey58")
            line.append(_bar(d.cost, max_cost, 24))
            line.append("  ")
            line.append(money(d.cost), style="green")
            console.print(line)
        console.print()
