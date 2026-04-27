"""
roadmap.py — Roadmap domain operations for opc-tools.

Parses and queries ROADMAP.md: get-phase, analyze, update-progress.
"""

from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    extract_first_field,
    find_phase_dir,
    list_phase_dirs,
    normalize_phase_name,
    opc_paths,
    output,
    safe_read,
)


_LOCALIZED_PHASE_LABEL = "\u9636\u6bb5"
_FULLWIDTH_COLON = "\uff1a"
_LOCALIZED_SUCCESS_CRITERIA_LABEL = "\u6210\u529f\u6807\u51c6"
_PHASE_HEADER_RE = re.compile(
    rf"^(?P<hashes>#{{2,4}})\s*(?:Phase|{_LOCALIZED_PHASE_LABEL})\s+"
    rf"(?P<num>\d+(?:\.\d+)?)(?:\s*[:{_FULLWIDTH_COLON}]\s*(?P<name>[^\n]+))?\s*$",
    re.IGNORECASE | re.MULTILINE,
)
_SUCCESS_CRITERIA_RE = re.compile(
    rf"\*\*(?:Success Criteria|{_LOCALIZED_SUCCESS_CRITERIA_LABEL})"
    rf"(?:\s*[:{_FULLWIDTH_COLON}])?\*\*(?:\s*[:{_FULLWIDTH_COLON}])?\s*\n"
    r"(?P<items>(?:\s*\d+\.\s*[^\n]+\n?)+)",
    re.IGNORECASE,
)


def _iter_phase_headers(content: str) -> Iterator[re.Match[str]]:
    return _PHASE_HEADER_RE.finditer(content)


def _phase_header_matches(match: re.Match[str], phase_num: str) -> bool:
    return normalize_phase_name(match.group("num")) == normalize_phase_name(phase_num)


def _phase_display_name(match: re.Match[str]) -> str:
    name = match.group("name")
    if name and name.strip():
        return name.strip()
    return match.group(0).lstrip("#").strip()


def _find_next_phase_header(content: str, start: int, max_level: int) -> re.Match[str] | None:
    for match in _PHASE_HEADER_RE.finditer(content, start):
        if len(match.group("hashes")) <= max_level:
            return match
    return None


def _extract_success_criteria(section: str) -> list[str]:
    match = _SUCCESS_CRITERIA_RE.search(section)
    if not match:
        return []
    return [
        re.sub(r"^\s*\d+\.\s*", "", line).strip()
        for line in match.group("items").strip().split("\n")
        if line.strip()
    ]


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

    header_match = next(
        (match for match in _iter_phase_headers(content) if _phase_header_matches(match, phase_num)),
        None,
    )

    if not header_match:
        # Fallback: check in summary checklist
        checklist = re.search(
            rf"-\s*\[[ x]\]\s*\*\*(?:Phase|{_LOCALIZED_PHASE_LABEL})\s+{escaped}"
            rf"(?:\s*[:{_FULLWIDTH_COLON}]\s*([^*]+))?\*\*",
            content, re.IGNORECASE,
        )
        if checklist:
            checklist_name = checklist.group(1).strip() if checklist.group(1) else f"Phase {phase_num}"
            output({
                "found": False,
                "phase_number": phase_num,
                "phase_name": checklist_name,
                "error": "malformed_roadmap",
                "message": f"Phase {phase_num} exists in summary but missing detail section.",
            }, raw, "")
        else:
            output({"found": False, "phase_number": phase_num}, raw, "")
        return

    phase_name = _phase_display_name(header_match)
    header_level = len(header_match.group("hashes"))
    header_index = header_match.start()

    # Find section end (next same-or-higher-level header)
    next_header = _find_next_phase_header(content, header_match.end(), header_level)
    section_end = next_header.start() if next_header else len(content)
    section = content[header_index:section_end].strip()

    goal = extract_first_field(section, "Goal", "\u76ee\u6807")
    criteria = _extract_success_criteria(section)
    requirements = extract_first_field(section, "Requirements", "\u9700\u6c42")

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

    phases: list[dict[str, Any]] = []

    for match in _iter_phase_headers(content):
        num = match.group("num")
        name = _phase_display_name(match)
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
