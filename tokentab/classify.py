"""Guess what a turn was doing, so the dashboard can say "you spent $40 on
debugging" instead of just "$40".
 
Deliberately dumb: no model calls, just which tools got used plus words in the
first user message. It's a hint, not a verdict, and it's easy to eyeball whether
it's roughly right.
"""

from __future__ import annotations

_EDIT_TOOLS = {"edit", "write", "str_replace", "multiedit", "applypatch", "apply_patch"}
_READ_TOOLS = {"read", "grep", "glob", "search", "websearch", "web_search", "ls"}


def classify(tool_names: list[str], user_text: str) -> str:
    tools = [t.lower() for t in tool_names]
    text = user_text.lower()

    def has(tool_set: set[str]) -> bool:
        return any(t in tool_set for t in tools)

    def said(*words: str) -> bool:
        return any(w in text for w in words)

    edited = has(_EDIT_TOOLS)
    ran_shell = any(t in ("bash", "shell", "run") for t in tools)

    if ran_shell and said("test", "pytest", "vitest", "jest", "npm test", "go test"):
        return "testing"

    if said("commit", "push", "merge", "rebase", "pull request", "git "):
        return "git"

    if said("plan", "how should", "what's the best way", "approach", "design the"):
        if not edited:
            return "planning"

    if edited:
        if said("bug", "fix", "error", "crash", "broken", "doesn't work", "not working"):
            return "debugging"
        if said("refactor", "rename", "clean up", "simplify", "tidy", "extract"):
            return "refactor"
        if said("add", "create", "implement", "build", "new feature", "support for"):
            return "feature"
        return "coding"

    if has(_READ_TOOLS):
        return "exploring"
    if not tools:
        return "chat"
    return "general"
