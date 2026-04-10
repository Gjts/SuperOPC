#!/usr/bin/env python3

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
import sys

from common import ensure_dir, get_tool_input, read_stdin_json


def main() -> int:
    payload = read_stdin_json()
    command = get_tool_input(payload).get("command", "")
    if not isinstance(command, str) or not command:
        return 0

    timestamp = datetime.now(timezone.utc).isoformat()
    log_dir = Path.cwd() / ".opc"
    log_file = log_dir / "audit.log"

    try:
        ensure_dir(log_dir)
        with log_file.open("a", encoding="utf-8") as handle:
            handle.write(f"[{timestamp}] {command}\n")
    except OSError:
        pass

    return 0


if __name__ == "__main__":
    sys.exit(main())
