"""
roadmap.py — Roadmap domain operations for opc-tools.

Parses and queries ROADMAP.md: get-phase, analyze, update-progress.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    find_phase_dir,
    list_phase_dirs,
    normalize_phase_name,
    opc_paths,
    output,
    safe_read,
)


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def dispatch_roadmap(args: list[str], cwd: Path, raw: bool) -> None:
    """Route roadmap subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "get-phase":
        if not rest:
            error("phase number required for roadmap get-phase")
        cmd_roadmap_get_phase(cwd, rest[0], raw)
    elif sub == "analyze":
        cmd_roadmap_analyze(cwd, raw)
    elif sub == "update-progress":
        if not rest:
            error("phase number required for roadmap update-progress")
        cmd_roadmap_update_progress(cwd, rest[0], raw)
    else:
        error(f"Unknown roadmap subcommand: {sub}\nAvailable: get-phase, analyze, update-progress")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_roadmap_get_phase(cwd: Path, phase_num: str, raw: bool) -> None:
    """Extract a phase section from ROADMAP.md."""
    roadmap_path = opc_paths(cwd)["roadmap"]
    if not roadmap_path.exists():
        output({"found": False, "error": "ROADMAP.md not found"}, raw, "")
        return

    content = safe_read(roadmap_path)
    escaped = re.escape(phase_num)

    # Match "## Phase X:", "### Phase X:", or "#### Phase X:"
    header_pattern = re.compile(
        rf"(#{2,4})\s*Phase\s+{escaped}:\s*([^\n]+)", re.IGNORECASE
    )
    header_match = header_pattern.search(content)

    if not header_match:
        # Fallback: check in summary checklist
        checklist = re.search(
            rf"-\s*\[[ x]\]\s*\*\*Phase\s+{escaped}:\s*([^*]+)\*\*",
            content, re.IGNORECASE,
        )
        if checklist:
            output({
                "found": False,
                "phase_number": phase_num,
                "phase_name": checklist.group(1).strip(),
                "error": "malformed_roadmap",
                "message": f"Phase {phase_num} exists in summary but missing detail section.",
            }, raw, "")
        else:
            output({"found": False, "phase_number": phase_num}, raw, "")
        return

    phase_name = header_match.group(2).strip()
    header_level = len(header_match.group(1))
    header_index = header_match.start()

    # Find section end (next same-or-higher-level header)
    rest = content[header_index:]
    next_header = re.search(rf"\n#{{{1},{header_level}}}\s+Phase\s+\d", rest[1:], re.IGNORECASE)
    section_end = header_index + 1 + next_header.start() if next_header else len(content)
    section = content[header_index:section_end].strip()

    # Extract goal
    goal_match = re.search(r"\*\*Goal(?::\*\*|\*\*:)\s*([^\n]+)", section, re.IGNORECASE)
    goal = goal_match.group(1).strip() if goal_match else None

    # Extract success criteria
    criteria_match = re.search(
        r"\*\*Success Criteria\*\*[^\n]*:\s*\n((?:\s*\d+\.\s*[^\n]+\n?)+)", section, re.IGNORECASE
    )
    criteria: list[str] = []
    if criteria_match:
        criteria = [
            re.sub(r"^\s*\d+\.\s*", "", line).strip()
            for line in criteria_match.group(1).strip().split("\n")
            if line.strip()
        ]

    # Extract requirements reference
    req_match = re.search(r"\*\*Requirements\*\*:\s*([^\n]*)", section, re.IGNORECASE)
    requirements = req_match.group(1).strip() if req_match else None

    output({
        "found": True,
        "phase_number": phase_num,
        "phase_name": phase_name,
        "goal": goal,
        "success_criteria": criteria,
        "requirements": requirements,
        "section": section,
    }, raw, section)


def cmd_roadmap_analyze(cwd: Path, raw: bool) -> None:
    """Full roadmap parse with disk status for each phase."""
    roadmap_path = opc_paths(cwd)["roadmap"]
    if not roadmap_path.exists():
        output({"error": "ROADMAP.md not found", "phases": []}, raw, "")
        return

    content = safe_read(roadmap_path)

    # Find all phase headers
    phase_pattern = re.compile(r"#{2,4}\s*Phase\s+(\d+(?:\.\d+)?):\s*([^\n]+)", re.IGNORECASE)
    phases: list[dict[str, Any]] = []

    for match in phase_pattern.finditer(content):
        num = match.group(1)
        name = match.group(2).strip()
        phase_dir = find_phase_dir(cwd, num)

        plans_count = 0
        summaries_count = 0
        has_verification = False

        if phase_dir:
            plans_count = len(list(phase_dir.glob("*PLAN.md")))
            summaries_count = len(list(phase_dir.glob("*SUMMARY.md")))
            has_verification = bool(list(phase_dir.glob("*VERIFICATION.md")))

        # Determine status
        if not phase_dir:
            status = "Not Started"
        elif plans_count == 0:
            status = "Pending"
        elif summaries_count < plans_count and summaries_count > 0:
            status = "In Progress"
        elif summaries_count >= plans_count and has_verification:
            status = "Complete"
        elif summaries_count >= plans_count:
            status = "Executed"
        else:
            status = "Planned"

        phases.append({
            "phase_number": num,
            "phase_name": name,
            "status": status,
            "plans": plans_count,
            "summaries": summaries_count,
            "has_verification": has_verification,
            "has_directory": phase_dir is not None,
        })

    # Summary stats
    total = len(phases)
    complete = sum(1 for p in phases if p["status"] == "Complete")
    in_progress = sum(1 for p in phases if p["status"] == "In Progress")

    result = {
        "total_phases": total,
        "complete": complete,
        "in_progress": in_progress,
        "phases": phases,
    }

    if raw:
        output(result, raw=True)
    else:
        lines = [f"Roadmap: {complete}/{total} complete, {in_progress} in progress\n"]
        for p in phases:
            icon = "✅" if p["status"] == "Complete" else "🔄" if p["status"] == "In Progress" else "⬜"
            lines.append(f"  {icon} Phase {p['phase_number']}: {p['phase_name']} [{p['status']}]")
        output(result, raw=False, text="\n".join(lines))


def cmd_roadmap_update_progress(cwd: Path, phase_num: str, raw: bool) -> None:
    """Update a phase's progress row in ROADMAP.md based on disk contents."""
    phase_dir = find_phase_dir(cwd, phase_num)
    if not phase_dir:
        error(f"Phase {phase_num} directory not found")

    plans_count = len(list(phase_dir.glob("*PLAN.md")))
    summaries_count = len(list(phase_dir.glob("*SUMMARY.md")))
    has_verification = bool(list(phase_dir.glob("*VERIFICATION.md")))

    roadmap_path = opc_paths(cwd)["roadmap"]
    if not roadmap_path.exists():
        error("ROADMAP.md not found")

    content = safe_read(roadmap_path)
    # Look for a progress table row for this phase
    row_pattern = re.compile(
        rf"\|\s*{re.escape(phase_num)}\s*\|.*\|",
        re.IGNORECASE,
    )
    match = row_pattern.search(content)
    if match:
        new_row = f"| {phase_num} | {plans_count} plans | {summaries_count} summaries | {'✅' if has_verification else '⬜'} |"
        content = content[:match.start()] + new_row + content[match.end():]
        roadmap_path.write_text(content, encoding="utf-8")

    output({
        "phase": phase_num,
        "plans": plans_count,
        "summaries": summaries_count,
        "has_verification": has_verification,
    }, raw, f"Phase {phase_num}: {plans_count}P/{summaries_count}S")
