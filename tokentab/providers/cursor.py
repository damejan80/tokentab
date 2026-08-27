"""STUB — not implemented yet.

This is the one provider left for you to write. Everything else parses flat
text/JSON logs; Cursor is different enough that it deserves its own care.

Where Cursor keeps its data (a SQLite database called state.vscdb):
    macOS   ~/Library/Application Support/Cursor/User/globalStorage/state.vscdb
    Linux   ~/.config/Cursor/User/globalStorage/state.vscdb
    Windows %APPDATA%/Cursor/User/globalStorage/state.vscdb

The catch: it's SQLite, not a text log. Good news for Python — sqlite3 is in the
standard library, so no extra dependency. Token counts live inside the
conversation blobs (look for keys under composerData / the prompt token
breakdown), and the numbers are Cursor's own estimates, so treat them as
approximate.

To make this real:
    1. open the db read-only with sqlite3
    2. pull each conversation's tokens + model + workspace
    3. map them into UsageRecord (see tokentab/types.py) and return the list

Until then this returns [] so the rest of the tool runs fine without Cursor.
If Cursor is installed we print a gentle nudge once, and nothing else.
"""

from __future__ import annotations

import os
import sys

from .shared import home

NAME = "cursor"
LABEL = "Cursor"

_warned = False


def _db_path():
    if sys.platform == "darwin":
        return home("Library", "Application Support", "Cursor", "User", "globalStorage", "state.vscdb")
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA") or str(home("AppData", "Roaming"))
        return home() / appdata / "Cursor" / "User" / "globalStorage" / "state.vscdb"
    return home(".config", "Cursor", "User", "globalStorage", "state.vscdb")


def collect() -> list:
    global _warned
    db = _db_path()

    if db.parent.is_dir() and not _warned:
        _warned = True
        # only mentioned once, and only if Cursor actually seems installed, so it
        # doesn't nag people who don't use it
        print(
            "note: Cursor data was found but the parser isn't implemented yet — "
            "skipping it. (see tokentab/providers/cursor.py)",
            file=sys.stderr,
        )

    # TODO(you): read the SQLite db and return real records.
    return []
