"""Codex stores rollout files under
    ~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl
(and older ones under ~/.codex/archived_sessions/).

The lines are event objects. Token usage shows up in "token_count" events, which
are CUMULATIVE across the session — so we diff consecutive events to get per-call
numbers instead of double counting. The working directory comes from a
session-meta event near the top of the file.
"""

from __future__ import annotations

import os

from ..classify import classify
from ..types import TokenCounts, UsageRecord
from .shared import EPOCH, home, pretty_project, to_date, try_json, walk_files

NAME = "codex"
LABEL = "Codex"


def _config_dir():
    override = os.environ.get("CODEX_HOME")
    return home(*override.split("/")) if override else home(".codex")


def _find_token_count(ev: dict):
    if ev.get("type") == "token_count":
        return ev.get("payload") or ev.get("info") or ev
    payload = ev.get("payload") or {}
    if payload.get("type") == "token_count":
        return payload.get("info") or payload
    nested = (payload.get("info") or {}).get("total_token_usage") or (ev.get("info") or {}).get("total_token_usage")
    return nested or None


def collect() -> list[UsageRecord]:
    roots = [_config_dir() / "sessions", _config_dir() / "archived_sessions"]
    records: list[UsageRecord] = []

    for root in roots:
        if not root.is_dir():
            continue

        for file in walk_files(root, lambda n: n.startswith("rollout-") and n.endswith(".jsonl")):
            try:
                text = file.read_text(encoding="utf-8")
            except OSError:
                continue

            lines = text.split("\n")
            project = "unknown"
            model = "unknown"
            first_user_text = ""
            tool_names: list[str] = []

            # context pass
            for line in lines:
                if not line.strip():
                    continue
                ev = try_json(line)
                if not isinstance(ev, dict):
                    continue
                if ev.get("cwd"):
                    project = pretty_project(ev["cwd"])
                if ev.get("model"):
                    model = ev["model"]
                payload = ev.get("payload") or {}
                if ev.get("type") == "function_call" or payload.get("type") == "function_call":
                    name = payload.get("name") or (ev.get("info") or {}).get("name")
                    if name:
                        tool_names.append(str(name))
                if (ev.get("type") == "message" or payload.get("role") == "user") and not first_user_text:
                    content = payload.get("content") or (ev.get("info") or {}).get("content")
                    if isinstance(content, str):
                        first_user_text = content[:500]

            activity = classify(tool_names, first_user_text)

            # usage pass — cumulative totals diffed into per-call deltas
            prev_in = prev_out = prev_cache = 0
            i = 0
            for line in lines:
                if not line.strip():
                    continue
                ev = try_json(line)
                if not isinstance(ev, dict):
                    continue
                tc = _find_token_count(ev)
                if not tc:
                    continue

                tot_in = tc.get("input_tokens", tc.get("input", 0)) or 0
                tot_out = tc.get("output_tokens", tc.get("output", 0)) or 0
                tot_cache = tc.get("cached_input_tokens", tc.get("cache_read", 0)) or 0

                d_in = max(0, tot_in - prev_in)
                d_out = max(0, tot_out - prev_out)
                d_cache = max(0, tot_cache - prev_cache)
                prev_in, prev_out, prev_cache = tot_in, tot_out, tot_cache

                if d_in + d_out + d_cache == 0:
                    continue

                records.append(
                    UsageRecord(
                        provider=NAME,
                        model=model,
                        project=project,
                        timestamp=to_date(ev.get("timestamp")) or EPOCH,
                        activity=activity,
                        id=f"{file}:{i}",
                        tokens=TokenCounts(input=d_in, output=d_out, cache_read=d_cache, cache_write=0),
                    )
                )
                i += 1

    return records
