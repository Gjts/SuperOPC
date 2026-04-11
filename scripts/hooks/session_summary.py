#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

from common import ensure_dir, read_stdin_json, session_id


def _read_json(file_path: Path) -> dict:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def _latest_handoff(opc_dir: Path) -> dict:
    return _read_json(opc_dir / "HANDOFF.json")


def _latest_state_snapshot(opc_dir: Path) -> dict:
    state_file = opc_dir / "STATE.md"
    if not state_file.exists():
        return {}

    try:
        lines = state_file.read_text(encoding="utf-8").splitlines()
    except OSError:
        return {}

    snapshot: dict[str, str] = {}
    for label in ("当前焦点", "状态", "最近活动", "上次会话", "停止于", "恢复文件"):
        for raw_line in lines:
            if raw_line.startswith(f"**{label}：**"):
                snapshot[label] = raw_line.split("**", 2)[-1].split("：", 1)[-1].strip()
                break
            if raw_line.startswith(f"{label}："):
                snapshot[label] = raw_line.split("：", 1)[1].strip()
                break
    return snapshot


def main() -> int:
    payload = read_stdin_json()
    timestamp = datetime.now(timezone.utc)
    safe_stamp = timestamp.isoformat().replace(":", "-").replace(".", "-")
    opc_dir = Path.cwd() / ".opc"
    session_dir = opc_dir / "sessions"
    session_file = session_dir / f"session-{safe_stamp}.json"
    handoff = _latest_handoff(opc_dir)
    state = _latest_state_snapshot(opc_dir)
    summary = {
        "timestamp": timestamp.isoformat(),
        "tool_name": payload.get("tool_name", "unknown"),
        "session_id": session_id(),
        "cwd": str(Path.cwd()),
        "handoffUpdatedAt": handoff.get("updatedAt", ""),
        "handoffNextStep": (handoff.get("nextSteps") or [""])[0] if isinstance(handoff.get("nextSteps"), list) else "",
        "stateStatus": state.get("状态", ""),
        "stateFocus": state.get("当前焦点", ""),
        "stopPoint": state.get("停止于", ""),
    }

    try:
        ensure_dir(session_dir)
        session_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
