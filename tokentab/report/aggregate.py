"""Turn a flat list of priced records into the grouped report the CLI and web
dashboard both render.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ..types import PricedRecord, TokenCounts

PERIODS = ("today", "week", "30days", "month", "all")


@dataclass
class DateRange:
    frm: datetime
    to: datetime


@dataclass
class Totals:
    cost: float = 0.0
    tokens: TokenCounts = field(default_factory=TokenCounts)
    calls: int = 0
    cache_hit_rate: float = 0.0


@dataclass
class Row:
    label: str
    cost: float = 0.0
    tokens: int = 0
    calls: int = 0


@dataclass
class DayRow:
    date: str
    cost: float = 0.0
    tokens: int = 0
    calls: int = 0


@dataclass
class Report:
    range: DateRange
    totals: Totals
    by_tool: list[Row]
    by_model: list[Row]
    by_project: list[Row]
    by_activity: list[Row]
    by_day: list[DayRow]


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _start_of_today() -> datetime:
    n = _now()
    return n.replace(hour=0, minute=0, second=0, microsecond=0)


def range_for(period: str) -> DateRange:
    to = _now()
    if period == "today":
        return DateRange(_start_of_today(), to)
    if period == "week":
        return DateRange(to - timedelta(days=7), to)
    if period == "30days":
        return DateRange(to - timedelta(days=30), to)
    if period == "month":
        return DateRange(to.replace(day=1, hour=0, minute=0, second=0, microsecond=0), to)
    # all
    return DateRange(datetime.fromtimestamp(0, tz=timezone.utc), to)


def parse_range(period: str, frm: str | None = None, to: str | None = None) -> DateRange:
    if not frm and not to:
        return range_for(period)

    def parse(s: str, end: bool = False) -> datetime:
        d = datetime.fromisoformat(s)
        if d.tzinfo is None:
            d = d.replace(tzinfo=timezone.utc)
        if end:
            d = d.replace(hour=23, minute=59, second=59, microsecond=999000)
        return d

    start = parse(frm) if frm else datetime.fromtimestamp(0, tz=timezone.utc)
    end = parse(to, end=True) if to else _now()
    if start > end:
        raise ValueError("--from is after --to")
    return DateRange(start, end)


def _day_key(d: datetime) -> str:
    return d.strftime("%Y-%m-%d")


def build_report(
    records: list[PricedRecord],
    rng: DateRange,
    project: str | None = None,
    exclude: list[str] | None = None,
) -> Report:
    exclude = exclude or []

    def keep(r: PricedRecord) -> bool:
        ts = r.timestamp
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
        if ts < rng.frm or ts > rng.to:
            return False
        if project and project.lower() not in r.project.lower():
            return False
        if any(x.lower() in r.project.lower() for x in exclude):
            return False
        return True

    in_range = [r for r in records if keep(r)]

    totals = Totals(calls=len(in_range))
    tools: dict[str, Row] = {}
    models: dict[str, Row] = {}
    projects: dict[str, Row] = {}
    activities: dict[str, Row] = {}
    days: dict[str, DayRow] = {}

    def bump(m: dict[str, Row], key: str, r: PricedRecord) -> None:
        row = m.get(key)
        if row is None:
            row = Row(label=key)
            m[key] = row
        row.cost += r.cost
        row.tokens += r.tokens.total()
        row.calls += 1

    for r in in_range:
        totals.cost += r.cost
        totals.tokens.input += r.tokens.input
        totals.tokens.output += r.tokens.output
        totals.tokens.cache_read += r.tokens.cache_read
        totals.tokens.cache_write += r.tokens.cache_write

        bump(tools, r.provider, r)
        bump(models, r.model, r)
        bump(projects, r.project, r)
        bump(activities, r.activity, r)

        ts = r.timestamp if r.timestamp.tzinfo else r.timestamp.replace(tzinfo=timezone.utc)
        key = _day_key(ts)
        d = days.get(key)
        if d is None:
            d = DayRow(date=key)
            days[key] = d
        d.cost += r.cost
        d.tokens += r.tokens.total()
        d.calls += 1

    input_side = totals.tokens.input + totals.tokens.cache_read
    totals.cache_hit_rate = (totals.tokens.cache_read / input_side) if input_side > 0 else 0.0

    by_cost = lambda rows: sorted(rows, key=lambda x: x.cost, reverse=True)

    return Report(
        range=rng,
        totals=totals,
        by_tool=by_cost(tools.values()),
        by_model=by_cost(models.values()),
        by_project=by_cost(projects.values()),
        by_activity=by_cost(activities.values()),
        by_day=sorted(days.values(), key=lambda d: d.date),
    )
