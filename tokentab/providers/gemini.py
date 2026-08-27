"""Gemini CLI keeps one JSON file per session at
    ~/.gemini/tmp/<project>/chats/session-*.json

Nice and civilised: a single JSON document with a list of messages, each carrying
real token counts. One gotcha — Gemini reports input INCLUSIVE of cached tokens,
so we subtract the cached part before pricing so we don't pay for the same tokens
twice.
"""

from __future__ import annotations

from ..classify import classify
from ..types import TokenCounts, UsageRecord
from .shared import EPOCH, home, pretty_project, to_date, try_json, walk_files

NAME = "gemini"
LABEL = "Gemini CLI"


def _derive_project(path) -> str:
    # .../tmp/<project>/chats/session-*.json -> <project>
    parts = str(path).replace("\\", "/").split("/")
    if "tmp" in parts:
        i = parts.index("tmp")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


def collect() -> list[UsageRecord]:
    root = home(".gemini", "tmp")
    if not root.is_dir():
        return []

    records: list[UsageRecord] = []

    for file in walk_files(root, lambda n: n.startswith("session-") and n.endswith(".json")):
        try:
            raw = file.read_text(encoding="utf-8")
        except OSError:
            continue
        doc = try_json(raw)
        messages = doc.get("messages") if isinstance(doc, dict) else None
        if not messages:
            continue

        project = pretty_project(_derive_project(file))

        first_user_text = ""
        tool_names: list[str] = []
        for m in messages:
            if m.get("role") == "user" and not first_user_text:
                first_user_text = (m.get("text") or "")[:500]
            for p in m.get("parts") or []:
                fc = p.get("functionCall")
                if fc and fc.get("name"):
                    tool_names.append(fc["name"])
        activity = classify(tool_names, first_user_text)

        for i, m in enumerate(messages):
            t = m.get("tokens")
            if not t:
                continue
            cached = t.get("cached", 0) or 0
            raw_input = t.get("input", 0) or 0
            fresh_input = max(0, raw_input - cached)  # input is inclusive of cache
            output = t.get("output", 0) or 0

            if fresh_input + output + cached == 0:
                continue

            records.append(
                UsageRecord(
                    provider=NAME,
                    model=m.get("model") or "gemini-2.5-pro",
                    project=project,
                    timestamp=to_date(m.get("timestamp")) or EPOCH,
                    activity=activity,
                    id=f"{file}:{i}",
                    tokens=TokenCounts(input=fresh_input, output=output, cache_read=cached, cache_write=0),
                )
            )

    return records
