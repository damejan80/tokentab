"""Small helpers the provider parsers lean on."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def home(*parts: str) -> Path:
    return Path.home().joinpath(*parts)


def try_json(text: str):
    """Parse one JSON value, returning None instead of raising."""
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def walk_files(root: Path, test) -> Iterator[Path]:
    """Yield every file under root whose name passes test(name).

    Skips anything unreadable rather than blowing up the whole run.
    """
    if not root.is_dir():
        return
    for dirpath, _dirs, files in os.walk(root):
        for name in files:
            if test(name):
                yield Path(dirpath) / name


def pretty_project(raw: str) -> str:
    """Tools encode the project path into a folder name by swapping slashes for
    dashes. We can't perfectly reverse that, but the last meaningful segment is a
    good label — "my-app" instead of a giant string.
    """
    if not raw:
        return "unknown"
    cleaned = raw.lstrip("-")
    parts = [p for p in cleaned.replace("\\", "/").replace("-", "/").split("/") if p]
    return parts[-1] if parts else "unknown"


def to_date(value) -> datetime | None:
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            # heuristic: seconds vs milliseconds
            secs = value / 1000 if value > 1e12 else value
            return datetime.fromtimestamp(secs, tz=timezone.utc)
        s = str(value).replace("Z", "+00:00")
        return datetime.fromisoformat(s)
    except (ValueError, OSError, OverflowError):
        return None


EPOCH = datetime.fromtimestamp(0, tz=timezone.utc)
