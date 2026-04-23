"""
profile.py — Developer profile via ProfileEngine (opc-tools domain).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

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
    from engine.profile_engine import ProfileEngine

    named = parse_named_args(rest, value_flags=["profile-dir"], bool_flags=[])
    pdir = named.get("profile-dir")
    profile_dir = Path(pdir).resolve() if isinstance(pdir, str) and pdir else None
    return ProfileEngine(profile_dir=profile_dir)


def _split_relaxed_pairs(raw: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    depth = 0
    quote: str | None = None

    for char in raw:
        if quote:
            current.append(char)
            if char == quote:
                quote = None
            continue
        if char in {"'", '"'}:
            quote = char
            current.append(char)
            continue
        if char == "[":
            depth += 1
            current.append(char)
            continue
        if char == "]":
            depth = max(0, depth - 1)
            current.append(char)
            continue
        if char == "," and depth == 0:
            item = "".join(current).strip()
            if item:
                parts.append(item)
            current = []
            continue
        current.append(char)

    item = "".join(current).strip()
    if item:
        parts.append(item)
    return parts


def _parse_signal_value(raw: str) -> Any:
    value = raw.strip().strip('"').strip("'")
    if not value:
        return ""
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item for item in (_parse_signal_value(part) for part in _split_relaxed_pairs(inner)) if item != ""]
    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False
    if re.fullmatch(r"-?\d+", value):
        return int(value)
    if re.fullmatch(r"-?\d+\.\d+", value):
        return float(value)
    return value


def parse_record_signals(raw: str) -> dict[str, Any]:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        payload = None
    if isinstance(payload, dict):
        return payload

    body = raw.strip()
    if body.startswith("{") and body.endswith("}"):
        body = body[1:-1].strip()
    if not body:
        return {}

    parsed: dict[str, Any] = {}
    for part in _split_relaxed_pairs(body):
        if ":" in part:
            key, value = part.split(":", 1)
        elif "=" in part:
            key, value = part.split("=", 1)
        else:
            raise ValueError(part)
        normalized_key = key.strip().strip('"').strip("'")
        if not normalized_key:
            raise ValueError(part)
        parsed[normalized_key] = _parse_signal_value(value)
    return parsed


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
            signals = parse_record_signals(sig)
        except ValueError:
            error("profile record: --signals must be a JSON object or key:value pairs")
    pe = _profile_engine(rest)
    pe.record_interaction(command=cmd, project=proj or "", signals=signals)
    output({"recorded": True, "command": cmd, "project": proj}, raw, "ok")
