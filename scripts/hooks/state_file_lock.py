#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

from common import ensure_dir, get_first_path, get_tool_input, read_stdin_json, session_id, write_json


LOCK_TIMEOUT_MS = 30000
LOCK_SUFFIX = ".lock"


def main() -> int:
    payload = read_stdin_json()
    file_path = get_first_path(get_tool_input(payload))
    if not file_path:
        return 0

    path_obj = Path(file_path)
    if not path_obj.name.upper().startswith("STATE"):
        return 0

    normalized = file_path.replace("\\", "/")
    if ".opc/" not in normalized and ".planning/" not in normalized:
        return 0

    lock_path = Path(f"{file_path}{LOCK_SUFFIX}")
    now_ms = int(time.time() * 1000)

    if lock_path.exists():
        try:
            lock_data = json.loads(lock_path.read_text(encoding="utf-8"))
            lock_age = now_ms - int(lock_data.get("timestamp", 0))
            if lock_age < LOCK_TIMEOUT_MS:
                locked_by = lock_data.get("agent", "unknown agent")
                additional_context = (
                    f'STATE FILE LOCK WARNING: {path_obj.name} is currently locked by "{locked_by}" '
                    f"({round(lock_age / 1000)}s ago). Another agent may be writing to this file. "
                    "To avoid conflicts, wait a few seconds and retry, or write to a different section. "
                    f"Lock will auto-expire after {LOCK_TIMEOUT_MS // 1000}s."
                )
                write_json(
                    {
                        "hookSpecificOutput": {
                            "hookEventName": "PreToolUse",
                            "additionalContext": additional_context,
                        }
                    }
                )
                return 0
        except Exception:
            pass

        try:
            lock_path.unlink()
        except OSError:
            pass

    lock_data = {
        "timestamp": now_ms,
        "agent": payload.get("agent_name") or session_id() or "unknown",
        "file": path_obj.name,
        "pid": os.getpid(),
    }

    try:
        ensure_dir(lock_path.parent)
        lock_path.write_text(json.dumps(lock_data, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
