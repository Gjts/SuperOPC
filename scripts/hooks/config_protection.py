#!/usr/bin/env python3

from __future__ import annotations

from pathlib import Path
import sys

from common import get_first_path, get_tool_input, read_stdin_json, write_message


CONFIG_FILES = {
    ".eslintrc",
    ".eslintrc.js",
    ".eslintrc.json",
    ".eslintrc.yml",
    "eslint.config.js",
    "eslint.config.mjs",
    ".prettierrc",
    ".prettierrc.js",
    ".prettierrc.json",
    "prettier.config.js",
    "prettier.config.mjs",
    "tsconfig.json",
    "tsconfig.build.json",
    ".stylelintrc",
    ".stylelintrc.json",
    "biome.json",
    "biome.jsonc",
    ".editorconfig",
}


def main() -> int:
    payload = read_stdin_json()
    file_path = get_first_path(get_tool_input(payload))
    if not file_path:
        return 0

    basename = Path(file_path).name
    if basename in CONFIG_FILES:
        write_message(
            f'SuperOPC: Modifying linter/formatter config "{basename}". '
            "Consider fixing the code to comply with existing rules instead of weakening the config."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
