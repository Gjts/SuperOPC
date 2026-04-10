#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import json
import sys

from common import ensure_dir, read_stdin_json, session_id


def main() -> int:
    payload = read_stdin_json()
    timestamp = datetime.now(timezone.utc)
    safe_stamp = timestamp.isoformat().replace(":", "-").replace(".", "-")
    session_dir = Path.cwd() / ".opc" / "sessions"
    session_file = session_dir / f"session-{safe_stamp}.json"
    summary = {
        "timestamp": timestamp.isoformat(),
        "tool_name": payload.get("tool_name", "unknown"),
        "session_id": session_id(),
    }

    try:
        ensure_dir(session_dir)
        session_file.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
