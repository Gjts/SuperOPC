"""
state.py — State domain operations for opc-tools.

Manages STATE.md: load, get, update, patch, json export, begin-phase.
Also handles todo listing.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    extract_field,
    load_config,
    now_iso,
    opc_dir,
    opc_paths,
    output,
    safe_read,
    to_posix,
)


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def dispatch_state(args: list[str], cwd: Path, raw: bool) -> None:
    """Route state subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "load":
        cmd_state_load(cwd, raw)
    elif sub == "get":
        cmd_state_get(cwd, rest[0] if rest else None, raw)
    elif sub == "update":
        if len(rest) < 2:
            error("state update requires <field> <value>")
        cmd_state_update(cwd, rest[0], " ".join(rest[1:]), raw)
    elif sub == "patch":
        patches = _parse_patch_args(rest)
        cmd_state_patch(cwd, patches, raw)
    elif sub == "json":
        cmd_state_json(cwd, raw)
    elif sub == "begin-phase":
        named = _extract_named(rest, ["phase", "name", "plans"])
        cmd_state_begin_phase(cwd, named, raw)
    elif sub == "advance-plan":
        cmd_state_advance_plan(cwd, raw)
    elif sub == "record-metric":
        named = _extract_named(rest, ["phase", "plan", "duration", "tasks", "files"])
        cmd_state_record_metric(cwd, named, raw)
    elif sub == "add-decision":
        named = _extract_named(rest, ["summary", "phase", "rationale"])
        cmd_state_add_decision(cwd, named, raw)
    elif sub == "add-blocker":
        named = _extract_named(rest, ["text"])
        cmd_state_add_blocker(cwd, named, raw)
    elif sub == "resolve-blocker":
        named = _extract_named(rest, ["text"])
        cmd_state_resolve_blocker(cwd, named, raw)
    elif sub == "record-session":
        named = _extract_named(rest, ["stopped-at"])
        cmd_state_record_session(cwd, named, raw)
    else:
        error(f"Unknown state subcommand: {sub}\nAvailable: load, get, update, patch, json, begin-phase, advance-plan, record-metric, add-decision, add-blocker, resolve-blocker, record-session")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _extract_named(args: list[str], keys: list[str]) -> dict[str, str | None]:
    """Extract --key value pairs from args."""
    result: dict[str, str | None] = {}
    for key in keys:
        flag = f"--{key}"
        try:
            idx = args.index(flag)
            if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
                result[key] = args[idx + 1]
            else:
                result[key] = None
        except ValueError:
            result[key] = None
    return result


def _parse_patch_args(args: list[str]) -> dict[str, str]:
    """Parse --field value pairs for state patch."""
    patches: dict[str, str] = {}
    i = 0
    while i < len(args):
        if args[i].startswith("--"):
            key = args[i][2:]
            if i + 1 < len(args) and not args[i + 1].startswith("--"):
                patches[key] = args[i + 1]
                i += 2
                continue
        i += 1
    return patches


def _read_state(cwd: Path) -> str:
    """Read STATE.md content or exit with error."""
    state_path = opc_paths(cwd)["state"]
    content = safe_read(state_path)
    if not content:
        error("STATE.md not found or empty")
    return content


def _write_state(cwd: Path, content: str) -> None:
    """Write STATE.md atomically."""
    state_path = opc_paths(cwd)["state"]
    state_path.write_text(content, encoding="utf-8")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_state_load(cwd: Path, raw: bool) -> None:
    """Load project config + state summary."""
    config = load_config(cwd)
    paths = opc_paths(cwd)

    state_raw = safe_read(paths["state"])
    state_exists = bool(state_raw)
    roadmap_exists = paths["roadmap"].exists()
    config_exists = paths["config"].exists()

    result = {
        "config": config,
        "state_exists": state_exists,
        "roadmap_exists": roadmap_exists,
        "config_exists": config_exists,
    }

    if raw:
        output(result, raw=True)
    else:
        lines = [
            f"model_profile={config.get('model_profile', 'balanced')}",
            f"commit_docs={config.get('commit_docs', True)}",
            f"config_exists={config_exists}",
            f"roadmap_exists={roadmap_exists}",
            f"state_exists={state_exists}",
        ]
        output(result, raw=False, text="\n".join(lines))


def cmd_state_get(cwd: Path, section: str | None, raw: bool) -> None:
    """Get STATE.md content or a specific section/field."""
    content = _read_state(cwd)

    if not section:
        output({"content": content}, raw, content)
        return

    # Try field extraction
    value = extract_field(content, section)
    if value:
        output({section: value}, raw, value)
        return

    # Try markdown section
    escaped = re.escape(section)
    match = re.search(rf"##\s*{escaped}\s*\n([\s\S]*?)(?=\n##|$)", content, re.IGNORECASE)
    if match:
        output({section: match.group(1).strip()}, raw, match.group(1).strip())
        return

    output({"error": f'Section or field "{section}" not found'}, raw, "")


def cmd_state_update(cwd: Path, field: str, value: str, raw: bool) -> None:
    """Update a single STATE.md field."""
    content = _read_state(cwd)
    updated, success = _replace_field(content, field, value)
    if success:
        _write_state(cwd, updated)
        output({"updated": field, "value": value}, raw, "true")
    else:
        output({"error": f"Field '{field}' not found in STATE.md"}, raw, "false")


def cmd_state_patch(cwd: Path, patches: dict[str, str], raw: bool) -> None:
    """Batch update STATE.md fields."""
    content = _read_state(cwd)
    updated_fields: list[str] = []
    failed_fields: list[str] = []

    for field, value in patches.items():
        content, success = _replace_field(content, field, value)
        if success:
            updated_fields.append(field)
        else:
            failed_fields.append(field)

    if updated_fields:
        _write_state(cwd, content)

    result = {"updated": updated_fields, "failed": failed_fields}
    output(result, raw, "true" if updated_fields else "false")


def cmd_state_json(cwd: Path, raw: bool) -> None:
    """Output STATE.md as structured JSON (parse all fields)."""
    content = _read_state(cwd)
    fields: dict[str, str | None] = {}
    known_fields = [
        "Project Name", "Current Focus", "Status",
        "Phase", "Total Phases", "Phase Name",
        "Current Plan", "Total Plans in Phase",
        "Recent Activity", "Last Session", "Stop Point", "Resume File",
    ]
    for f in known_fields:
        fields[f] = extract_field(content, f)
    output(fields, raw=True)


def cmd_state_begin_phase(cwd: Path, named: dict[str, str | None], raw: bool) -> None:
    """Update STATE.md for a new phase start."""
    phase = named.get("phase")
    name = named.get("name", "")
    plans = named.get("plans", "0")

    if not phase:
        error("--phase is required for begin-phase")

    content = _read_state(cwd)
    replacements = {
        "Status": "执行中",
        "Phase": phase,
        "Phase Name": name or "",
        "Current Plan": "1",
        "Total Plans in Phase": plans or "0",
        "Recent Activity": f"开始阶段 {phase}: {name}",
        "Last Session": now_iso(),
    }

    for field, value in replacements.items():
        content, _ = _replace_field(content, field, str(value))

    _write_state(cwd, content)
    output({"phase": phase, "name": name, "status": "executing"}, raw, f"Phase {phase} started")


def cmd_state_advance_plan(cwd: Path, raw: bool) -> None:
    """Increment the current plan counter."""
    content = _read_state(cwd)
    current = extract_field(content, "Current Plan")
    if current and current.isdigit():
        new_val = str(int(current) + 1)
        content, _ = _replace_field(content, "Current Plan", new_val)
        _write_state(cwd, content)
        output({"current_plan": new_val}, raw, new_val)
    else:
        output({"error": "Current Plan field not found or not numeric"}, raw, "false")


def cmd_state_record_metric(cwd: Path, named: dict[str, str | None], raw: bool) -> None:
    """Record execution metrics for a phase/plan."""
    content = _read_state(cwd)
    phase = named.get("phase", "?")
    plan = named.get("plan", "?")
    duration = named.get("duration", "?")

    metric_line = f"- Phase {phase} Plan {plan}: {duration}"
    if named.get("tasks"):
        metric_line += f" ({named['tasks']} tasks)"
    if named.get("files"):
        metric_line += f" ({named['files']} files)"

    # Append to Performance Metrics section
    metrics_section = re.search(r"(##\s*Performance Metrics.*?)(\n##|\Z)", content, re.DOTALL | re.IGNORECASE)
    if metrics_section:
        insert_point = metrics_section.end(1)
        content = content[:insert_point] + "\n" + metric_line + content[insert_point:]
        _write_state(cwd, content)

    output({"recorded": True, "metric": metric_line}, raw, metric_line)


def cmd_state_add_decision(cwd: Path, named: dict[str, str | None], raw: bool) -> None:
    """Add a decision to STATE.md decisions section."""
    summary_text = named.get("summary", "")
    if not summary_text:
        error("--summary required for add-decision")

    content = _read_state(cwd)
    decision_line = f"- [{now_iso()[:10]}] {summary_text}"
    if named.get("phase"):
        decision_line += f" (Phase {named['phase']})"
    if named.get("rationale"):
        decision_line += f" — {named['rationale']}"

    content = _append_to_section(content, "Decisions", decision_line)
    _write_state(cwd, content)
    output({"added": True, "decision": decision_line}, raw, decision_line)


def cmd_state_add_blocker(cwd: Path, named: dict[str, str | None], raw: bool) -> None:
    """Add a blocker to STATE.md."""
    text = named.get("text", "")
    if not text:
        error("--text required for add-blocker")

    content = _read_state(cwd)
    blocker_line = f"- ⚠️ {text}"
    content = _append_to_section(content, "Blockers", blocker_line)
    _write_state(cwd, content)
    output({"added": True, "blocker": text}, raw, text)


def cmd_state_resolve_blocker(cwd: Path, named: dict[str, str | None], raw: bool) -> None:
    """Remove a blocker from STATE.md."""
    text = named.get("text", "")
    if not text:
        error("--text required for resolve-blocker")

    content = _read_state(cwd)
    escaped = re.escape(text)
    new_content = re.sub(rf"- ⚠️ {escaped}\n?", "", content)
    if new_content != content:
        _write_state(cwd, new_content)
        output({"resolved": True, "blocker": text}, raw, "true")
    else:
        output({"resolved": False, "error": "Blocker not found"}, raw, "false")


def cmd_state_record_session(cwd: Path, named: dict[str, str | None], raw: bool) -> None:
    """Update session continuity fields."""
    content = _read_state(cwd)
    stopped_at = named.get("stopped-at", "")

    replacements = {"Last Session": now_iso()}
    if stopped_at:
        replacements["Stop Point"] = stopped_at

    for field, value in replacements.items():
        content, _ = _replace_field(content, field, value)

    _write_state(cwd, content)
    output({"recorded": True, "timestamp": now_iso()}, raw, "true")


# ---------------------------------------------------------------------------
# Todo commands
# ---------------------------------------------------------------------------

def cmd_list_todos(cwd: Path, area: str | None, raw: bool) -> None:
    """Count and enumerate pending todos."""
    todos_dir = opc_dir(cwd) / "todos" / "pending"
    todos: list[dict[str, str]] = []

    if todos_dir.exists():
        for f in sorted(todos_dir.glob("*.md")):
            content = safe_read(f)
            title_m = re.search(r"^title:\s*(.+)$", content, re.MULTILINE)
            area_m = re.search(r"^area:\s*(.+)$", content, re.MULTILINE)
            created_m = re.search(r"^created:\s*(.+)$", content, re.MULTILINE)

            todo_area = area_m.group(1).strip() if area_m else "general"
            if area and todo_area != area:
                continue

            todos.append({
                "file": f.name,
                "title": title_m.group(1).strip() if title_m else "Untitled",
                "area": todo_area,
                "created": created_m.group(1).strip() if created_m else "unknown",
                "path": to_posix(f.relative_to(cwd)),
            })

    result = {"count": len(todos), "todos": todos}
    output(result, raw, str(len(todos)))


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _replace_field(content: str, field: str, value: str) -> tuple[str, bool]:
    """Replace a field value in STATE.md. Returns (new_content, success)."""
    escaped = re.escape(field)
    # Try **Field:** bold format
    bold_pattern = re.compile(rf"(\*\*{escaped}:\*\*\s*)(.*)", re.IGNORECASE)
    if bold_pattern.search(content):
        return bold_pattern.sub(rf"\g<1>{value}", content, count=1), True

    # Try plain Field: format
    plain_pattern = re.compile(rf"(^{escaped}:\s*)(.*)", re.IGNORECASE | re.MULTILINE)
    if plain_pattern.search(content):
        return plain_pattern.sub(rf"\g<1>{value}", content, count=1), True

    return content, False


def _append_to_section(content: str, section_name: str, line: str) -> str:
    """Append a line to a ## section in STATE.md."""
    pattern = re.compile(rf"(##\s*{re.escape(section_name)}.*?)(\n##|\Z)", re.DOTALL | re.IGNORECASE)
    match = pattern.search(content)
    if match:
        insert_point = match.end(1)
        return content[:insert_point] + "\n" + line + content[insert_point:]
    # Section not found — append at end
    return content.rstrip() + f"\n\n## {section_name}\n\n{line}\n"
