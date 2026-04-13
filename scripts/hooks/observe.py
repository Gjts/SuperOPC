#!/usr/bin/env python3
"""
observe.py — PostToolUse observation hook for SuperOPC Continuous Learning.

Captures tool-use metadata to ~/.opc/learnings/observations.jsonl.
This is the perception layer of the learning pipeline:
  observe (this hook) → detect_patterns → evolve_instincts → context_injection

Lightweight and async-safe: appends one JSON line per invocation.
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

from bridge import emit_hook_event  # noqa: E402

LEARNINGS_DIR = Path.home() / ".opc" / "learnings"
OBS_FILE = LEARNINGS_DIR / "observations.jsonl"


def main() -> None:
    tool_name = os.environ.get("CLAUDE_TOOL_NAME", "")
    tool_input_raw = os.environ.get("CLAUDE_TOOL_INPUT", "{}")
    session_id = os.environ.get("CLAUDE_SESSION_ID", "")

    if not tool_name:
        return

    try:
        tool_input = json.loads(tool_input_raw)
    except json.JSONDecodeError:
        tool_input = {}

    action = _extract_action(tool_name, tool_input)
    context = _extract_context(tool_name, tool_input)
    project = _detect_project()

    record = {
        "ts": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "tool": tool_name,
        "action": action,
        "context": context[:200],
        "project": project,
        "meta": {
            "session": session_id[:16] if session_id else "",
        },
    }

    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)
    try:
        with open(OBS_FILE, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except OSError:
        pass

    emit_hook_event("learning.observed", {
        "tool": tool_name,
        "action": action,
        "project": project,
    })


def _extract_action(tool: str, inp: dict) -> str:
    """Derive a short action label from tool name and input."""
    if tool == "Bash":
        cmd = inp.get("command", "")
        if cmd.startswith("git "):
            parts = cmd.split()
            return f"git-{parts[1]}" if len(parts) > 1 else "git"
        if cmd.startswith("npm ") or cmd.startswith("pnpm ") or cmd.startswith("yarn "):
            return "package-manager"
        if cmd.startswith("python ") or cmd.startswith("pytest"):
            return "python-exec"
        if cmd.startswith("dotnet"):
            return "dotnet-exec"
        return "shell"
    if tool in ("Edit", "MultiEdit"):
        path = inp.get("file_path", "")
        if path.endswith(".test.ts") or path.endswith("_test.py") or path.endswith(".spec.ts"):
            return "edit-test"
        return "edit-code"
    if tool == "Write":
        return "write-file"
    if tool == "Read":
        return "read-file"
    if tool in ("Glob", "Grep"):
        return "search"
    if tool == "Task":
        return "subagent"
    return tool.lower()


def _extract_context(tool: str, inp: dict) -> str:
    """Extract a short context string for the observation."""
    if tool in ("Edit", "MultiEdit", "Write", "Read"):
        return inp.get("file_path", "")[-80:]
    if tool == "Bash":
        return inp.get("command", "")[:80]
    if tool in ("Glob", "Grep"):
        return inp.get("pattern", inp.get("query", ""))[:80]
    return ""


def _detect_project() -> str:
    """Detect current project from CWD or .opc/ presence."""
    cwd = Path.cwd()
    for candidate in [cwd] + list(cwd.parents):
        if (candidate / ".opc").is_dir():
            return candidate.name
        if (candidate / ".git").is_dir():
            return candidate.name
    return cwd.name


if __name__ == "__main__":
    main()
