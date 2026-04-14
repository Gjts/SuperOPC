"""
intel.py — Codebase intelligence (IntelEngine) opc-tools domain.
"""

from __future__ import annotations

from pathlib import Path

from cli.core import error, opc_root, output


def dispatch_intel(args: list[str], cwd: Path, raw: bool) -> None:
    if not args:
        error("intel subcommand required: status | query | validate | snapshot | diff | refresh")
    sub = args[0]
    rest = args[1:]

    root = opc_root(cwd)
    from intel_engine import IntelEngine

    eng = IntelEngine(project_dir=root)

    if sub == "status":
        output(eng.status(), raw, None)
    elif sub == "query":
        if not rest:
            error("intel query requires <term>")
        output(eng.query(rest[0]), raw, None)
    elif sub == "validate":
        output(eng.validate(), raw, None)
    elif sub == "snapshot":
        path = eng.take_snapshot()
        output({"snapshot": str(path)}, raw, str(path))
    elif sub == "diff":
        output(eng.diff(), raw, None)
    elif sub == "refresh":
        output(eng.refresh(), raw, None)
    else:
        error("Unknown intel subcommand\nAvailable: status, query, validate, snapshot, diff, refresh")
