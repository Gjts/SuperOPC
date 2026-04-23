#!/usr/bin/env python3
"""
convert.py — Convert SuperOPC skills/agents/commands into runtime-specific formats.

Reads all markdown source files from skills/, agents/, commands/ and outputs
converted files to integrations/<runtime>/.
"""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from convert_renderers import convert_runtime, detect_runtimes, print_detected_runtimes
from convert_runtime_registry import DEFAULT_OUT, REPO_ROOT, RUNTIME_ORDER, TODAY, VALID_TOOLS
from convert_sources import collect_sources


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Convert SuperOPC formats for Claude Code and other runtimes.")
    parser.add_argument("--tool", choices=VALID_TOOLS, default="all", help="Runtime to generate, all runtimes, or auto-detect")
    parser.add_argument("--out", default=str(DEFAULT_OUT), help="Output directory for generated integrations")
    parser.add_argument("--detect", action="store_true", help="Print detected runtimes before conversion")
    return parser.parse_args(argv)


def resolve_runtimes(tool: str, detected: list[str]) -> list[str]:
    if tool == "all":
        return list(RUNTIME_ORDER)
    if tool == "auto":
        return detected or ["claude-code"]
    return [tool]


def main(argv: list[str]) -> int:
    args = parse_args(argv)
    out_dir = Path(args.out).resolve()
    detected = detect_runtimes()

    print("\nSuperOPC Format Converter")
    print(f"  Repo:   {REPO_ROOT}")
    print(f"  Output: {out_dir}")
    print(f"  Tool:   {args.tool}")
    print(f"  Date:   {TODAY}")
    if args.detect or args.tool == "auto":
        print_detected_runtimes(detected)
    print()

    sources = collect_sources()
    skill_count = sum(1 for source in sources if source.kind == "skill")
    agent_count = sum(1 for source in sources if source.kind == "agent")
    command_count = sum(1 for source in sources if source.kind == "command")
    print(f"  Found: {skill_count} skills, {agent_count} agents, {command_count} commands\n")

    runtimes = resolve_runtimes(args.tool, detected)
    total = 0
    for runtime in runtimes:
        count = convert_runtime(runtime, sources, out_dir)
        print(f"  [OK] {runtime}: {count} items converted")
        total += count

    print(f"\n  Done. Total: {total} conversions across {len(runtimes)} runtime(s).\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
