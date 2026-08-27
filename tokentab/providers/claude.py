"""Claude Code writes one .jsonl file per session under
    ~/.claude/projects/<encoded-path>/<session-id>.jsonl

Each line is a JSON object; the ones we care about are assistant turns — they
carry the model name, a usage block with token counts, and any tool_use blocks.
This is the friendliest format of the bunch, so it's a good first read if you're
trying to understand how a provider parser works.
"""

from __future__ import annotations

import os

from ..classify import classify
from ..types import TokenCounts, UsageRecord
from .shared import EPOCH, home, pretty_project, to_date, try_json, walk_files


def _config_dir():
    override = os.environ.get("CLAUDE_CONFIG_DIR")
    return home(*override.split("/")) if override else home(".claude")


NAME = "claude"
LABEL = "Claude Code"


def _extract_text(content) -> str:
    if not content:
        return ""
    parts = [c.get("text", "") for c in content if c.get("type") == "text"]
    return " ".join(parts)[:500]


def _derive_project(path) -> str:
    # .../projects/<encoded>/<session>.jsonl -> <encoded>
    parts = str(path).replace("\\", "/").split("/")
    if "projects" in parts:
        i = parts.index("projects")
        if i + 1 < len(parts):
            return parts[i + 1]
    return "unknown"


def collect() -> list[UsageRecord]:
    root = _config_dir() / "projects"
    if not root.is_dir():
        return []

    records: list[UsageRecord] = []
    seen: set[str] = set()

    for file in walk_files(root, lambda n: n.endswith(".jsonl")):
        project = pretty_project(_derive_project(file))

        try:
            text = file.read_text(encoding="utf-8")
        except OSError:
            continue

        lines = text.split("\n")

        # first pass: first user message (for activity) + tools used this session
        first_user_text = ""
        tool_names: list[str] = []
        for line in lines:
            if not line.strip():
                continue
            obj = try_json(line)
            msg = obj.get("message") if isinstance(obj, dict) else None
            if not msg:
                continue
            if msg.get("role") == "user" and not first_user_text:
                first_user_text = _extract_text(msg.get("content"))
            for block in msg.get("content") or []:
                if block.get("type") == "tool_use" and block.get("name"):
                    tool_names.append(block["name"])
        activity = classify(tool_names, first_user_text)

        # second pass: token usage from assistant turns
        for line in lines:
            if not line.strip():
                continue
            obj = try_json(line)
            msg = obj.get("message") if isinstance(obj, dict) else None
            usage = msg.get("usage") if msg else None
            if not usage:
                continue

            rec_id = msg.get("id") or f"{file}:{len(records)}"
            if rec_id in seen:
                continue
            seen.add(rec_id)

            records.append(
                UsageRecord(
                    provider=NAME,
                    model=msg.get("model") or "unknown",
                    project=project,
                    timestamp=to_date(obj.get("timestamp")) or EPOCH,
                    activity=activity,
                    id=rec_id,
                    tokens=TokenCounts(
                        input=usage.get("input_tokens", 0),
                        output=usage.get("output_tokens", 0),
                        cache_read=usage.get("cache_read_input_tokens", 0),
                        cache_write=usage.get("cache_creation_input_tokens", 0),
                    ),
                )
            )

    return records
