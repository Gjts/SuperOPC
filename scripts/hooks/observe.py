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
from datetime import datetime, timezone
from pathlib import Path

from bridge import emit_hook_event  # noqa: E402

LEARNINGS_DIR = Path.home() / ".opc" / "learnings"
OBS_FILE = LEARNINGS_DIR / "observations.jsonl"
SKILL_ROUTING_SINK = LEARNINGS_DIR / "skill_routing.jsonl"


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

    # Mirror intent_router audit log into the long-term learning sink.
    try:
        added = sync_skill_routing()
        if added:
            emit_hook_event(
                "learning.routing_synced",
                {"added": added, "project": project},
            )
    except Exception:
        # Never let observation break the hook.
        pass


def sync_skill_routing(project_root: Path | None = None) -> int:
    """Copy new records from .opc/routing/<today>.jsonl into
    ~/.opc/learnings/skill_routing.jsonl. Deduplicates by input_hash.

    Returns the number of newly appended records.
    """
    project_root = project_root or _project_root()
    date_key = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    src = project_root / ".opc" / "routing" / f"{date_key}.jsonl"
    if not src.exists():
        return 0

    LEARNINGS_DIR.mkdir(parents=True, exist_ok=True)

    seen: set[str] = set()
    if SKILL_ROUTING_SINK.exists():
        try:
            for line in SKILL_ROUTING_SINK.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                rec = json.loads(line)
                h = rec.get("input_hash")
                if h:
                    seen.add(h)
        except (OSError, json.JSONDecodeError):
            pass

    appended = 0
    try:
        with SKILL_ROUTING_SINK.open("a", encoding="utf-8") as sink:
            for line in src.read_text(encoding="utf-8").splitlines():
                if not line.strip():
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                h = rec.get("input_hash")
                if not h or h in seen:
                    continue
                rec.setdefault("project", project_root.name)
                sink.write(json.dumps(rec, ensure_ascii=False) + "\n")
                seen.add(h)
                appended += 1
    except OSError:
        pass
    return appended


def _project_root() -> Path:
    """Walk up CWD to find the project root (marked by .opc/ or .git/)."""
    cwd = Path.cwd()
    for candidate in [cwd] + list(cwd.parents):
        if (candidate / ".opc").is_dir() or (candidate / ".git").is_dir():
            return candidate
    return cwd


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
