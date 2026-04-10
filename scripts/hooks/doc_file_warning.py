#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

from common import get_first_path, get_tool_input, read_stdin_json, write_message


RECOGNIZED_DOCS = {
    "README.md",
    "CONTRIBUTING.md",
    "CHANGELOG.md",
    "SECURITY.md",
    "LICENSE",
    "CLAUDE.md",
    "AGENTS.md",
    "ROADMAP.md",
    "CODE_OF_CONDUCT.md",
    "ARCHITECTURE.md",
}
RECOGNIZED_DIRS = ("docs/", "skills/", "agents/", "commands/", ".opc/")


def main() -> int:
    payload = read_stdin_json()
    file_path = get_first_path(get_tool_input(payload))
    if not file_path or not file_path.endswith(".md"):
        return 0

    basename = Path(file_path).name
    normalized = file_path.replace("\\", "/")
    is_recognized = basename in RECOGNIZED_DOCS or any(part in normalized for part in RECOGNIZED_DIRS)
    if not is_recognized:
        write_message(
            f'SuperOPC: Creating "{basename}" outside standard paths. '
            "Consider placing docs in docs/, skills in skills/, or using a recognized root file."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
