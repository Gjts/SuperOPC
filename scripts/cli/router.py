"""
router.py — Main CLI router for opc-tools.

Parses top-level command and dispatches to domain modules.
Supports --raw for machine-readable JSON output and --cwd for sandbox operation.
"""

from __future__ import annotations

import sys
from pathlib import Path

from cli.core import error, set_pick_field


# ---------------------------------------------------------------------------
# Arg parsing helpers
# ---------------------------------------------------------------------------

def parse_named_args(
    args: list[str],
    value_flags: list[str] | None = None,
    bool_flags: list[str] | None = None,
) -> dict[str, str | bool | None]:
    """Extract --flag <value> and --flag (boolean) pairs from args."""
    result: dict[str, str | bool | None] = {}
    for flag in (value_flags or []):
        try:
            idx = args.index(f"--{flag}")
            if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
                result[flag] = args[idx + 1]
            else:
                result[flag] = None
        except ValueError:
            result[flag] = None
    for flag in (bool_flags or []):
        result[flag] = f"--{flag}" in args
    return result


def consume_cwd(args: list[str]) -> tuple[Path, list[str]]:
    """Extract --cwd from args, return (resolved_cwd, remaining_args)."""
    cwd = Path.cwd()
    remaining = list(args)

    # --cwd=<value> form
    for i, arg in enumerate(remaining):
        if arg.startswith("--cwd="):
            cwd = Path(arg.split("=", 1)[1]).resolve()
            remaining.pop(i)
            break
    else:
        # --cwd <value> form
        try:
            idx = remaining.index("--cwd")
            if idx + 1 < len(remaining):
                cwd = Path(remaining[idx + 1]).resolve()
                remaining.pop(idx + 1)
                remaining.pop(idx)
        except ValueError:
            pass

    if not cwd.is_dir():
        error(f"Invalid --cwd: {cwd}")
    return cwd, remaining


def has_raw(args: list[str]) -> bool:
    """Check if --raw is present."""
    return "--raw" in args


# ---------------------------------------------------------------------------
# Help text
# ---------------------------------------------------------------------------

HELP_TEXT = """\
opc-tools — SuperOPC CLI utility for workflow operations

Usage: python opc-tools <command> [subcommand] [args] [--raw] [--cwd <dir>]

State Operations:
  state load                          Load project config + state summary
  state get [section]                 Get STATE.md content or specific section/field
  state update <field> <value>        Update a STATE.md field
  state patch --field1 val1 ...       Batch update STATE.md fields
  state json                          Output STATE.md as structured JSON
  state begin-phase --phase N --name S  Update STATE.md for new phase start

Phase Operations:
  phase list [--type plans|summaries] List phase directories or files
  phase next-decimal <phase>          Calculate next decimal phase number
  phase add <description>             Append new phase to roadmap + create dir
  phase complete <phase>              Mark phase done, update state + roadmap

Roadmap Operations:
  roadmap get-phase <phase>           Extract phase section from ROADMAP.md
  roadmap analyze                     Full roadmap parse with disk status

Config Operations:
  config get [key]                    Get config value (full config or specific key)
  config set <key> <value>            Update a config value
  config list                         List all valid config keys

Verify Operations:
  verify summary <path>               Verify a SUMMARY.md file
  verify plan-structure <path>        Check PLAN.md structure + tasks
  verify phase-completeness <phase>   Check all plans have summaries
  verify consistency                  Check phase numbering, disk/roadmap sync
  verify health [--repair]            Check .opc/ integrity, optionally repair

Profile Operations:
  profile show [--injection]          Show developer profile (or context injection)
  profile export [--dir <path>]       Export USER-PROFILE.md
  profile record --command <cmd>      Record an interaction (optional --project, --signals JSON or key:value pairs)

Research Operations:
  research feed --query <topic>       Fetch multi-source feed into .opc/
  research insights [--feed <path>]   Generate structured insights JSON from feed
  research methods list               Query built-in methodology database
  research methods show <id>          Show methodology details
  research run --query <topic>        Run full pipeline and write .opc/research report

Intel Operations:
  intel status                        Intel file freshness status
  intel query <term>                  Search across .opc/intel/*.json
  intel validate                       Validate intel file schema
  intel snapshot                       Record snapshot for future diff
  intel diff                           Diff against last snapshot
  intel refresh                        Rebuild intel indexes and snapshot

Template Operations:
  template fill summary --phase N     Create pre-filled SUMMARY.md
  template fill plan --phase N        Create pre-filled PLAN.md
  template fill verification --phase N  Create pre-filled VERIFICATION.md

Init (Compound) Operations:
  init execute-phase <phase>          All context for execute-phase workflow
  init plan-phase <phase>             All context for plan-phase workflow
  init new-project                    All context for new-project workflow
  init quick <description>            All context for quick workflow
  init resume                         All context for resume workflow
  init verify-work <phase>            All context for verify-work workflow

Utility Operations:
  generate-slug <text>                Convert text to URL-safe slug
  current-timestamp [full|date|filename]  Get formatted timestamp
  list-todos [area]                   Count and enumerate pending todos
  path-exists <path>                  Check file/directory existence

Security Operations:
  security validate-path <path>       Check path for traversal attacks
  security scan-injection <text>      Check text for prompt injection patterns

Global Flags:
  --raw                               Machine-readable JSON output
  --cwd <dir>                         Override working directory
  --pick <field>                      Extract single field from JSON output
  help                                Show this help message
"""


# ---------------------------------------------------------------------------
# Main router
# ---------------------------------------------------------------------------

def main() -> None:
    argv = sys.argv[1:] if len(sys.argv) > 1 else []

    if not argv or argv[0] in ("help", "--help", "-h"):
        print(HELP_TEXT)
        sys.exit(0)

    cwd, args = consume_cwd(argv)
    raw = has_raw(args)
    # Remove --raw from args for cleaner downstream parsing
    args = [a for a in args if a != "--raw"]

    # Extract --pick for field extraction
    pick_field: str | None = None
    if "--pick" in args:
        idx = args.index("--pick")
        if idx + 1 < len(args):
            pick_field = args[idx + 1]
            args = args[:idx] + args[idx + 2:]
        else:
            error("--pick requires a field name")

    if pick_field and not raw:
        error("--pick requires --raw")

    command = args[0] if args else ""
    sub_args = args[1:]

    set_pick_field(pick_field)
    try:
        _dispatch(command, sub_args, cwd, raw, pick_field)
    finally:
        set_pick_field(None)


def _dispatch(command: str, args: list[str], cwd: Path, raw: bool, pick: str | None) -> None:
    """Route to the correct domain module."""
    # Lazy imports to keep startup fast
    if command == "state":
        from cli.state import dispatch_state
        dispatch_state(args, cwd, raw)

    elif command == "config":
        from cli.config import dispatch_config
        dispatch_config(args, cwd, raw)

    elif command == "phase":
        from cli.phase import dispatch_phase
        dispatch_phase(args, cwd, raw)

    elif command == "roadmap":
        from cli.roadmap import dispatch_roadmap
        dispatch_roadmap(args, cwd, raw)

    elif command == "verify":
        from cli.verify import dispatch_verify
        dispatch_verify(args, cwd, raw)

    elif command == "template":
        from cli.template import dispatch_template
        dispatch_template(args, cwd, raw)

    elif command == "init":
        from cli.init import dispatch_init
        dispatch_init(args, cwd, raw)

    elif command == "security":
        from cli.security import dispatch_security
        dispatch_security(args, cwd, raw)

    elif command == "profile":
        from cli.profile import dispatch_profile
        dispatch_profile(args, cwd, raw)

    elif command == "research":
        from cli.research import dispatch_research
        dispatch_research(args, cwd, raw)

    elif command == "intel":
        from cli.intel import dispatch_intel
        dispatch_intel(args, cwd, raw)

    elif command == "generate-slug":
        from cli.core import generate_slug, output
        text = args[0] if args else ""
        if not text:
            error("text required for slug generation")
        slug = generate_slug(text)
        output({"slug": slug}, raw, slug)

    elif command == "current-timestamp":
        from cli.core import now_iso, output
        fmt = args[0] if args else "full"
        from datetime import datetime, timezone
        now = datetime.now(timezone.utc)
        if fmt == "date":
            ts = now.strftime("%Y-%m-%d")
        elif fmt == "filename":
            ts = now.isoformat().replace(":", "-").split(".")[0]
        else:
            ts = now.isoformat().replace("+00:00", "Z")
        output({"timestamp": ts}, raw, ts)

    elif command == "list-todos":
        from cli.state import cmd_list_todos
        area = args[0] if args else None
        cmd_list_todos(cwd, area, raw)

    elif command == "path-exists":
        from cli.core import output
        target = args[0] if args else ""
        if not target:
            error("path required")
        p = Path(target) if Path(target).is_absolute() else cwd / target
        exists = p.exists()
        output({"exists": exists, "path": str(p)}, raw, str(exists).lower())

    else:
        error(f"Unknown command: {command}\nRun 'opc-tools help' for available commands.")
