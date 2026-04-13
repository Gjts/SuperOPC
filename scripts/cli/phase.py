"""
phase.py — Phase domain operations for opc-tools.

Manages phase directories: list, next-decimal, add, complete.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    extract_field,
    find_phase_dir,
    generate_slug,
    list_phase_dirs,
    normalize_phase_name,
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

def dispatch_phase(args: list[str], cwd: Path, raw: bool) -> None:
    """Route phase subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "list":
        file_type = None
        phase_filter = None
        for i, a in enumerate(rest):
            if a == "--type" and i + 1 < len(rest):
                file_type = rest[i + 1]
            if a == "--phase" and i + 1 < len(rest):
                phase_filter = rest[i + 1]
        cmd_phase_list(cwd, file_type, phase_filter, raw)

    elif sub == "next-decimal":
        if not rest:
            error("phase number required for next-decimal")
        cmd_phase_next_decimal(cwd, rest[0], raw)

    elif sub == "add":
        if not rest:
            error("description required for phase add")
        phase_id = None
        for i, a in enumerate(rest):
            if a == "--id" and i + 1 < len(rest):
                phase_id = rest[i + 1]
        desc = " ".join(a for a in rest if not a.startswith("--") and a != phase_id)
        cmd_phase_add(cwd, desc, phase_id, raw)

    elif sub == "complete":
        if not rest:
            error("phase number required for phase complete")
        cmd_phase_complete(cwd, rest[0], raw)

    elif sub == "find":
        if not rest:
            error("phase number required for phase find")
        cmd_phase_find(cwd, rest[0], raw)

    elif sub == "status":
        if not rest:
            error("phase number required for phase status")
        cmd_phase_status(cwd, rest[0], raw)

    else:
        error(f"Unknown phase subcommand: {sub}\nAvailable: list, next-decimal, add, complete, find, status")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_phase_list(cwd: Path, file_type: str | None, phase_filter: str | None, raw: bool) -> None:
    """List phase directories or files within phases."""
    dirs = list_phase_dirs(cwd)

    if phase_filter:
        normalized = normalize_phase_name(phase_filter)
        dirs = [d for d in dirs if _phase_matches(d.name, normalized)]

    if file_type:
        files: list[str] = []
        for d in dirs:
            for f in sorted(d.iterdir()):
                if not f.is_file():
                    continue
                if file_type == "plans" and (f.name.endswith("-PLAN.md") or f.name == "PLAN.md"):
                    files.append(to_posix(f.relative_to(cwd)))
                elif file_type == "summaries" and (f.name.endswith("-SUMMARY.md") or f.name == "SUMMARY.md"):
                    files.append(to_posix(f.relative_to(cwd)))
                elif file_type == "all":
                    files.append(to_posix(f.relative_to(cwd)))
        output({"files": files, "count": len(files)}, raw, "\n".join(files))
    else:
        dir_names = [d.name for d in dirs]
        output({"directories": dir_names, "count": len(dir_names)}, raw, "\n".join(dir_names))


def cmd_phase_next_decimal(cwd: Path, base_phase: str, raw: bool) -> None:
    """Calculate the next decimal phase number (e.g. 3 → 3.1 or 3.2)."""
    normalized = normalize_phase_name(base_phase)
    phases_dir = opc_dir(cwd) / "phases"

    existing_decimals: set[int] = set()
    base_exists = False

    if phases_dir.exists():
        for d in phases_dir.iterdir():
            if not d.is_dir():
                continue
            match = re.match(r"(\d+(?:\.\d+)?)", d.name)
            if match:
                name_norm = normalize_phase_name(match.group(1))
                if name_norm == normalized:
                    base_exists = True
                decimal_match = re.match(rf"^{re.escape(normalized)}\.(\d+)", name_norm)
                if decimal_match:
                    existing_decimals.add(int(decimal_match.group(1)))

    # Also check ROADMAP.md for planned decimals
    roadmap_path = opc_paths(cwd)["roadmap"]
    if roadmap_path.exists():
        roadmap_content = safe_read(roadmap_path)
        for m in re.finditer(rf"Phase\s+0*{re.escape(normalized)}\.(\d+)", roadmap_content, re.IGNORECASE):
            existing_decimals.add(int(m.group(1)))

    if existing_decimals:
        next_decimal = f"{normalized}.{max(existing_decimals) + 1}"
    else:
        next_decimal = f"{normalized}.1"

    existing_list = sorted(f"{normalized}.{d}" for d in existing_decimals)
    output(
        {"found": base_exists, "base_phase": normalized, "next": next_decimal, "existing": existing_list},
        raw,
        next_decimal,
    )


def cmd_phase_add(cwd: Path, description: str, phase_id: str | None, raw: bool) -> None:
    """Add a new phase directory and optionally update ROADMAP.md."""
    phases_dir = opc_dir(cwd) / "phases"
    phases_dir.mkdir(parents=True, exist_ok=True)

    # Determine next phase number
    if phase_id:
        num = normalize_phase_name(phase_id)
    else:
        existing = list_phase_dirs(cwd)
        if existing:
            last_match = re.match(r"(\d+)", existing[-1].name)
            num = str(int(last_match.group(1)) + 1) if last_match else "1"
        else:
            num = "1"

    slug = generate_slug(description)
    dir_name = f"{num.zfill(2)}-{slug}"
    phase_path = phases_dir / dir_name
    phase_path.mkdir(exist_ok=True)

    # Append to ROADMAP.md if it exists
    roadmap_path = opc_paths(cwd)["roadmap"]
    if roadmap_path.exists():
        content = safe_read(roadmap_path)
        new_section = f"\n### Phase {num}: {description}\n\n**Goal:** TBD\n**Requirements:** TBD\n"
        roadmap_path.write_text(content.rstrip() + "\n" + new_section, encoding="utf-8")

    output(
        {"phase_number": num, "directory": dir_name, "path": to_posix(phase_path.relative_to(cwd))},
        raw,
        dir_name,
    )


def cmd_phase_complete(cwd: Path, phase_num: str, raw: bool) -> None:
    """Mark a phase as complete: update STATE.md and ROADMAP.md."""
    phase_dir = find_phase_dir(cwd, phase_num)
    if not phase_dir:
        error(f"Phase {phase_num} directory not found")

    # Count plans and summaries
    plans = list(phase_dir.glob("*-PLAN.md")) + list(phase_dir.glob("PLAN.md"))
    summaries = list(phase_dir.glob("*-SUMMARY.md")) + list(phase_dir.glob("SUMMARY.md"))

    # Update STATE.md
    state_path = opc_paths(cwd)["state"]
    if state_path.exists():
        content = safe_read(state_path)
        from cli.state import _replace_field
        content, _ = _replace_field(content, "Status", "阶段完成")
        content, _ = _replace_field(content, "Recent Activity", f"阶段 {phase_num} 完成")
        content, _ = _replace_field(content, "Last Session", now_iso())
        state_path.write_text(content, encoding="utf-8")

    # Update ROADMAP.md checkbox
    roadmap_path = opc_paths(cwd)["roadmap"]
    if roadmap_path.exists():
        content = safe_read(roadmap_path)
        pattern = re.compile(
            rf"(- \[)\s*(\]\s*\*\*Phase\s+{re.escape(phase_num)}:)",
            re.IGNORECASE,
        )
        if pattern.search(content):
            content = pattern.sub(r"\1x\2", content)
            roadmap_path.write_text(content, encoding="utf-8")

    output(
        {"phase": phase_num, "plans": len(plans), "summaries": len(summaries), "status": "complete"},
        raw,
        f"Phase {phase_num} marked complete ({len(plans)} plans, {len(summaries)} summaries)",
    )


def cmd_phase_find(cwd: Path, phase_num: str, raw: bool) -> None:
    """Find a phase directory by number."""
    phase_dir = find_phase_dir(cwd, phase_num)
    if phase_dir:
        # Gather inventory
        plans = [f.name for f in phase_dir.glob("*PLAN.md")]
        summaries = [f.name for f in phase_dir.glob("*SUMMARY.md")]
        has_verification = any(phase_dir.glob("*VERIFICATION.md"))
        has_research = (phase_dir / "RESEARCH.md").exists() or any(phase_dir.glob("*RESEARCH.md"))
        has_context = (phase_dir / "CONTEXT.md").exists() or any(phase_dir.glob("*CONTEXT.md"))

        output({
            "found": True,
            "directory": to_posix(phase_dir.relative_to(cwd)),
            "phase_number": normalize_phase_name(phase_num),
            "plans": plans,
            "summaries": summaries,
            "plan_count": len(plans),
            "summary_count": len(summaries),
            "has_verification": has_verification,
            "has_research": has_research,
            "has_context": has_context,
        }, raw, to_posix(phase_dir.relative_to(cwd)))
    else:
        output({"found": False, "phase_number": phase_num}, raw, "")


def cmd_phase_status(cwd: Path, phase_num: str, raw: bool) -> None:
    """Determine phase status (Pending/Planned/In Progress/Executed/Complete)."""
    phase_dir = find_phase_dir(cwd, phase_num)
    if not phase_dir:
        output({"phase": phase_num, "status": "Not Found"}, raw, "not_found")
        return

    plans = list(phase_dir.glob("*PLAN.md"))
    summaries = list(phase_dir.glob("*SUMMARY.md"))
    verifications = list(phase_dir.glob("*VERIFICATION.md"))

    if not plans:
        status = "Pending"
    elif len(summaries) < len(plans) and len(summaries) > 0:
        status = "In Progress"
    elif len(summaries) < len(plans):
        status = "Planned"
    elif verifications:
        # Check verification status
        v_content = safe_read(verifications[0])
        if re.search(r"status:\s*passed", v_content, re.IGNORECASE):
            status = "Complete"
        elif re.search(r"status:\s*gaps_found", v_content, re.IGNORECASE):
            status = "Executed"
        else:
            status = "Executed"
    else:
        status = "Executed"

    output({"phase": phase_num, "status": status, "plans": len(plans), "summaries": len(summaries)}, raw, status)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _phase_matches(dir_name: str, normalized: str) -> bool:
    """Check if a directory name matches a phase number."""
    match = re.match(r"(\d+(?:\.\d+)?)", dir_name)
    if match:
        return normalize_phase_name(match.group(1)) == normalized
    return False
