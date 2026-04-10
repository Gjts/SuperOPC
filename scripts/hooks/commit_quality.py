#!/usr/bin/env python3

from __future__ import annotations

import re
import sys

from common import get_tool_input, read_stdin_json, write_message


CONVENTIONAL_PATTERN = re.compile(
    r"^(feat|fix|docs|style|refactor|perf|test|build|ci|chore|revert)(\(.+\))?!?:\s.+"
)
SECRET_PATTERNS = [
    re.compile(r"sk-[a-zA-Z0-9]{20,}"),
    re.compile(r"ghp_[a-zA-Z0-9]{36}"),
    re.compile(r"AKIA[0-9A-Z]{16}"),
    re.compile(r"[a-zA-Z0-9+/]{40,}={0,2}"),
]


def main() -> int:
    payload = read_stdin_json()
    command = get_tool_input(payload).get("command", "")
    if not isinstance(command, str) or not re.search(r"\bgit\s+commit\b", command):
        return 0

    warnings: list[str] = []
    match = re.search(r"-m\s+[\"']([^\"']+)[\"']", command)
    if match:
        message = match.group(1)
        if not CONVENTIONAL_PATTERN.match(message):
            warnings.append(
                "Commit message does not follow Conventional Commits format.\n"
                "  Expected: type(scope): description\n"
                "  Example:  feat(skills): add pricing skill"
            )
        if any(pattern.search(message) for pattern in SECRET_PATTERNS):
            write_message("SuperOPC: Potential secret detected in commit message. Review before committing.")
            return 2

    if warnings:
        write_message("SuperOPC commit quality:\n" + "\n".join(f"  - {item}" for item in warnings))

    return 0


if __name__ == "__main__":
    sys.exit(main())
