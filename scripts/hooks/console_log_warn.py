#!/usr/bin/env python3

from __future__ import annotations

import re
import sys

from common import get_first_content, get_tool_input, read_stdin_json, write_message


DEBUG_PATTERNS = [
    re.compile(r"console\.log\("),
    re.compile(r"console\.debug\("),
    re.compile(r"debugger;"),
    re.compile(r"print\(\s*f?[\"']"),
]


def main() -> int:
    payload = read_stdin_json()
    content = get_first_content(get_tool_input(payload))
    if not content:
        return 0

    if any(pattern.search(content) for pattern in DEBUG_PATTERNS):
        write_message(
            "SuperOPC: Debug statement detected in edited content. "
            "Remember to remove console.log/debugger/print before committing."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
