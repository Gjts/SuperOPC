#!/usr/bin/env python3

from __future__ import annotations

import re
import sys

from common import get_tool_input, read_stdin_json, write_message


def main() -> int:
    payload = read_stdin_json()
    command = get_tool_input(payload).get("command", "")

    if isinstance(command, str) and re.search(r"\bgit\s+push\b", command):
        write_message(
            "SuperOPC: About to push. Checklist:\n"
            "  1. Tests pass?\n"
            "  2. No debug statements left?\n"
            "  3. Commit messages follow Conventional Commits?\n"
            "  4. No secrets in committed files?"
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
