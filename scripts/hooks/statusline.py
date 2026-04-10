#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import re
import sys
import tempfile
import time
from pathlib import Path

from common import read_stdin_json


AUTO_COMPACT_BUFFER_PCT = 16.5


def read_current_task(workspace_dir: Path, session: str) -> str:
    state_path = workspace_dir / ".opc" / "STATE.md"
    if state_path.exists():
        try:
            content = state_path.read_text(encoding="utf-8")
            match = re.search(r"##\s*(?:Current|当前任务|当前)[^\n]*\n+(?:[-*]\s*)?(.+)", content, re.IGNORECASE)
            if match:
                return match.group(1).strip()[:60]
        except OSError:
            pass

    if session:
        claude_dir = Path(os.environ.get("CLAUDE_CONFIG_DIR", str(Path.home() / ".claude")))
        todos_dir = claude_dir / "todos"
        if todos_dir.exists():
            try:
                candidates = [
                    path
                    for path in todos_dir.iterdir()
                    if path.name.startswith(session) and "-agent-" in path.name and path.suffix == ".json"
                ]
                candidates.sort(key=lambda item: item.stat().st_mtime, reverse=True)
                if candidates:
                    todos = json.loads(candidates[0].read_text(encoding="utf-8"))
                    for todo in todos:
                        if todo.get("status") == "in_progress":
                            return str(todo.get("activeForm", ""))[:60]
            except Exception:
                pass

    return ""


def build_context_segment(session: str, remaining: float | int | None) -> str:
    if remaining is None:
        return ""

    usable_remaining = max(
        0.0,
        ((float(remaining) - AUTO_COMPACT_BUFFER_PCT) / (100 - AUTO_COMPACT_BUFFER_PCT)) * 100,
    )
    used = max(0, min(100, round(100 - usable_remaining)))

    if session and "/" not in session and "\\" not in session and ".." not in session:
        bridge_path = Path(tempfile.gettempdir()) / f"opc-ctx-{session}.json"
        bridge_data = {
            "session_id": session,
            "remaining_percentage": remaining,
            "used_pct": used,
            "timestamp": int(time.time()),
        }
        try:
            bridge_path.write_text(json.dumps(bridge_data, ensure_ascii=False), encoding="utf-8")
        except OSError:
            pass

    filled = used // 10
    bar = ("█" * filled) + ("░" * (10 - filled))

    if used < 50:
        return f" \x1b[32m{bar} {used}%\x1b[0m"
    if used < 65:
        return f" \x1b[33m{bar} {used}%\x1b[0m"
    if used < 80:
        return f" \x1b[38;5;208m{bar} {used}%\x1b[0m"
    return f" \x1b[5;31mALERT {bar} {used}%\x1b[0m"


def read_update_segment() -> str:
    cache_file = Path.home() / ".cache" / "superopc" / "update-check.json"
    if not cache_file.exists():
        return ""

    try:
        cache = json.loads(cache_file.read_text(encoding="utf-8"))
        if cache.get("update_available"):
            return "\x1b[33mupdate available\x1b[0m │ "
    except Exception:
        pass
    return ""


def main() -> int:
    data = read_stdin_json()
    model = str((data.get("model") or {}).get("display_name") or "Claude")
    workspace_dir = Path(str((data.get("workspace") or {}).get("current_dir") or Path.cwd()))
    session = str(data.get("session_id") or "")
    remaining = ((data.get("context_window") or {}).get("remaining_percentage"))

    context_segment = build_context_segment(session, remaining)
    task = read_current_task(workspace_dir, session)
    update_segment = read_update_segment()
    dirname = workspace_dir.name or str(workspace_dir)

    if task:
        sys.stdout.write(
            f"{update_segment}\x1b[2m{model}\x1b[0m │ \x1b[1m{task}\x1b[0m │ \x1b[2m{dirname}\x1b[0m{context_segment}"
        )
    else:
        sys.stdout.write(f"{update_segment}\x1b[2m{model}\x1b[0m │ \x1b[2m{dirname}\x1b[0m{context_segment}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
