#!/usr/bin/env python3

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def find_opc_dir(start_dir: Path) -> Path | None:
    current = start_dir.resolve()

    if current.name == ".opc" and current.exists():
        return current

    for candidate in (current, *current.parents):
        opc_dir = candidate / ".opc"
        if opc_dir.exists() and opc_dir.is_dir():
            return opc_dir

    return None


def read_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(file_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def write_json(file_path: Path, payload: dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def console_safe_text(text: str) -> str:
    return text.replace("¥", "CNY ").replace("￥", "CNY ")


def write_console_text(text: str, *, stream: Any | None = None) -> None:
    target = stream or sys.stdout
    normalized = console_safe_text(text)
    try:
        target.write(normalized)
        return
    except UnicodeEncodeError:
        encoding = getattr(target, "encoding", None) or "utf-8"
    safe = normalized.encode(encoding, errors="replace").decode(encoding, errors="replace")
    target.write(safe)
