"""
profile.py — Developer profile via ProfileEngine (opc-tools domain).
"""

from __future__ import annotations

import json
from pathlib import Path

from cli.core import error, output
from cli.router import parse_named_args


def dispatch_profile(args: list[str], cwd: Path, raw: bool) -> None:
    if not args:
        error("profile subcommand required: show | export | record")
    sub = args[0]
    rest = args[1:]

    if sub == "show":
        cmd_profile_show(cwd, rest, raw)
    elif sub == "export":
        cmd_profile_export(cwd, rest, raw)
    elif sub == "record":
        cmd_profile_record(cwd, rest, raw)
    else:
        error("Unknown profile subcommand\nAvailable: show, export, record")


def _profile_engine(rest: list[str]):
    from profile_engine import ProfileEngine

    named = parse_named_args(rest, value_flags=["profile-dir"], bool_flags=[])
    pdir = named.get("profile-dir")
    profile_dir = Path(pdir).resolve() if isinstance(pdir, str) and pdir else None
    return ProfileEngine(profile_dir=profile_dir)


def cmd_profile_show(cwd: Path, rest: list[str], raw: bool) -> None:
    injection_only = "--injection" in rest
    pe = _profile_engine(rest)
    if injection_only:
        output(pe.get_context_injection(), raw, None)
    else:
        p = pe.profile
        output(
            {
                "developer_profile": {
                    "communication_style": p.communication_style,
                    "decision_pattern": p.decision_pattern,
                    "debugging_preference": p.debugging_preference,
                    "ux_aesthetic": p.ux_aesthetic,
                    "learning_style": p.learning_style,
                    "explanation_depth": p.explanation_depth,
                    "tech_stack_affinity": p.tech_stack_affinity,
                    "friction_triggers": p.friction_triggers,
                    "interaction_count": p.interaction_count,
                    "projects_seen": p.projects_seen,
                    "preferred_commands": p.preferred_commands,
                    "updated_at": p.updated_at,
                }
            },
            raw,
            None,
        )


def cmd_profile_export(cwd: Path, rest: list[str], raw: bool) -> None:
    named = parse_named_args(rest, value_flags=["profile-dir", "dir"], bool_flags=[])
    pe = _profile_engine(rest)
    out_dir = named.get("dir") or named.get("profile-dir")
    target = Path(out_dir).resolve() if isinstance(out_dir, str) and out_dir else None
    path = pe.save_markdown(target)
    output({"exported": str(path)}, raw, str(path))


def cmd_profile_record(cwd: Path, rest: list[str], raw: bool) -> None:
    named = parse_named_args(rest, value_flags=["command", "project", "signals"], bool_flags=[])
    cmd = named.get("command")
    if not isinstance(cmd, str) or not cmd:
        error("profile record requires --command <slash-command>")
    proj = named.get("project") if isinstance(named.get("project"), str) else ""
    signals: dict | None = None
    sig = named.get("signals")
    if isinstance(sig, str) and sig.strip():
        try:
            signals = json.loads(sig)
        except json.JSONDecodeError:
            error("profile record: --signals must be JSON object")
    pe = _profile_engine(rest)
    pe.record_interaction(command=cmd, project=proj or "", signals=signals)
    output({"recorded": True, "command": cmd, "project": proj}, raw, "ok")
