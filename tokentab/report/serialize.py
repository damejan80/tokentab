"""Turn a Report into plain dicts the JSON encoder and the web API can emit.

The web page's JS expects camelCase keys (byTool, cacheRead, …) so we match that
here and use the same shape for both --json output and /api/report.
"""

from __future__ import annotations

from .aggregate import Report


def report_to_dict(report: Report) -> dict:
    t = report.totals
    return {
        "range": {
            "from": report.range.frm.isoformat(),
            "to": report.range.to.isoformat(),
        },
        "totals": {
            "cost": t.cost,
            "tokens": {
                "input": t.tokens.input,
                "output": t.tokens.output,
                "cacheRead": t.tokens.cache_read,
                "cacheWrite": t.tokens.cache_write,
            },
            "calls": t.calls,
            "cacheHitRate": t.cache_hit_rate,
        },
        "byTool": [_row(r) for r in report.by_tool],
        "byModel": [_row(r) for r in report.by_model],
        "byProject": [_row(r) for r in report.by_project],
        "byActivity": [_row(r) for r in report.by_activity],
        "byDay": [{"date": d.date, "cost": d.cost, "tokens": d.tokens, "calls": d.calls} for d in report.by_day],
    }


def _row(r) -> dict:
    return {"label": r.label, "cost": r.cost, "tokens": r.tokens, "calls": r.calls}
