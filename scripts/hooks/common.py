#!/usr/bin/env python3

from __future__ import annotations

import json
import os
import sys
from pathlib import Path
from typing import Any


def read_stdin_json() -> dict[str, Any]:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def get_tool_input(payload: dict[str, Any]) -> dict[str, Any]:
    value = payload.get("tool_input")
    return value if isinstance(value, dict) else {}


def get_first_path(tool_input: dict[str, Any]) -> str:
    for key in ("file_path", "path"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def get_first_content(tool_input: dict[str, Any]) -> str:
    for key in ("new_string", "content"):
        value = tool_input.get(key)
        if isinstance(value, str):
            return value
    return ""


def write_message(message: str) -> None:
    sys.stdout.write(f"{message}\n")


def write_json(payload: dict[str, Any]) -> None:
    sys.stdout.write(json.dumps(payload, ensure_ascii=False))


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def session_id() -> str:
    return os.environ.get("CLAUDE_SESSION_ID", "unknown")
