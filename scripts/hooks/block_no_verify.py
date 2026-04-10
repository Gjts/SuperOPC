#!/usr/bin/env python3

import re
import sys

from common import get_tool_input, read_stdin_json, write_message


def main() -> int:
    payload = read_stdin_json()
    command = get_tool_input(payload).get("command", "")

    if isinstance(command, str) and re.search(r"--no-verify", command):
        write_message(
            "SuperOPC: --no-verify flag detected. "
            "Pre-commit hooks exist for a reason - they protect code quality. "
            "Remove --no-verify and fix the underlying issue instead."
        )
        return 2

    return 0


if __name__ == "__main__":
    sys.exit(main())
