#!/usr/bin/env python3

from __future__ import annotations

import sys

from common import get_first_path, get_tool_input, read_stdin_json, write_message


def main() -> int:
    payload = read_stdin_json()
    file_path = get_first_path(get_tool_input(payload))
    if file_path:
        write_message(
            f'SuperOPC: Ensure you have read "{file_path}" before editing. '
            "Reading first prevents edit failures from outdated content assumptions."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
