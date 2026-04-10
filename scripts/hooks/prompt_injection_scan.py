#!/usr/bin/env python3

from __future__ import annotations

import re
import sys

from common import get_first_content, get_tool_input, read_stdin_json, write_message


INJECTION_PATTERNS = [
    re.compile(r"ignore\s+(all\s+)?previous\s+instructions", re.IGNORECASE),
    re.compile(r"you\s+are\s+now\s+a\s+different", re.IGNORECASE),
    re.compile(r"disregard\s+(all\s+)?(prior|previous)", re.IGNORECASE),
    re.compile(r"system\s*:\s*you\s+are", re.IGNORECASE),
    re.compile(r"\[INST\]", re.IGNORECASE),
    re.compile(r"<\|im_start\|>", re.IGNORECASE),
    re.compile("\u200B"),
    re.compile("\u200C"),
    re.compile("\u200D"),
    re.compile("\uFEFF"),
]


def main() -> int:
    payload = read_stdin_json()
    content = get_first_content(get_tool_input(payload))
    if not content:
        return 0

    findings = [pattern.pattern for pattern in INJECTION_PATTERNS if pattern.search(content)]
    if findings:
        write_message(
            "SuperOPC: Potential prompt injection pattern detected in file content.\n"
            f"  Patterns: {', '.join(findings[:3])}\n"
            "  This is advisory - review the content to confirm it is intentional."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
