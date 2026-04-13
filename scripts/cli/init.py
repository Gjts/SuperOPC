"""
init.py — Compound init commands for opc-tools.

Provides all-in-one context loading for workflow bootstrapping:
execute-phase, plan-phase, new-project, quick, resume, verify-work.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    extract_field,
    find_phase_dir,
    generate_slug,
    list_phase_dirs,
    load_config,
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

def dispatch_init(args: list[str], cwd: Path, raw: bool) -> None:
    """Route init subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "execute-phase":
        if not rest:
            error("phase number required for init execute-phase")
        cmd_init_execute_phase(cwd, rest[0], raw)
    elif sub == "plan-phase":
        if not rest:
            error("phase number required for init plan-phase")
        cmd_init_plan_phase(cwd, rest[0], raw)
    elif sub == "new-project":
        cmd_init_new_project(cwd, raw)
    elif sub == "quick":
        desc = " ".join(rest)
        cmd_init_quick(cwd, desc, raw)
    elif sub == "resume":
        cmd_init_resume(cwd, raw)
    elif sub == "verify-work":
        if not rest:
            error("phase number required for init verify-work")
        cmd_init_verify_work(cwd, rest[0], raw)
    elif sub == "progress":
        cmd_init_progress(cwd, raw)
    elif sub == "todos":
        area = rest[0] if rest else None
        cmd_init_todos(cwd, area, raw)
    else:
        error(f"Unknown init workflow: {sub}\nAvailable: execute-phase, plan-phase, new-project, quick, resume, verify-work, progress, todos")


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _with_project_root(cwd: Path, result: dict[str, Any]) -> dict[str, Any]:
    """Inject project_root and agent installation status."""
    result["project_root"] = to_posix(cwd)

    # Check agent installation
    agents_dir = Path(__file__).resolve().parent.parent.parent / "agents"
    result["agents_installed"] = agents_dir.exists() and any(agents_dir.glob("*.md"))

    # Inject response_language
    config = load_config(cwd)
    if config.get("response_language"):
        result["response_language"] = config["response_language"]

    return result


def _get_phase_info(cwd: Path, phase_num: str) -> dict[str, Any]:
    """Gather phase information for init commands."""
    phase_dir = find_phase_dir(cwd, phase_num)
    normalized = normalize_phase_name(phase_num)

    if phase_dir:
        plans = sorted(f.name for f in phase_dir.glob("*PLAN.md"))
        summaries = sorted(f.name for f in phase_dir.glob("*SUMMARY.md"))
        incomplete = [p for p in plans if p.replace("-PLAN.md", "-SUMMARY.md").replace("PLAN.md", "SUMMARY.md") not in summaries]

        # Extract phase name from directory
        name_match = re.match(r"\d+(?:\.\d+)?-(.+)", phase_dir.name)
        phase_name = name_match.group(1).replace("-", " ").title() if name_match else ""

        return {
            "found": True,
            "directory": to_posix(phase_dir.relative_to(cwd)),
            "phase_number": normalized,
            "phase_name": phase_name,
            "phase_slug": generate_slug(phase_name),
            "plans": plans,
            "summaries": summaries,
            "incomplete_plans": incomplete,
            "plan_count": len(plans),
            "incomplete_count": len(incomplete),
            "has_verification": bool(list(phase_dir.glob("*VERIFICATION.md"))),
            "has_research": (phase_dir / "RESEARCH.md").exists(),
            "has_context": (phase_dir / "CONTEXT.md").exists(),
        }
    else:
        return {
            "found": False,
            "directory": None,
            "phase_number": normalized,
            "phase_name": "",
            "plans": [],
            "summaries": [],
            "incomplete_plans": [],
            "plan_count": 0,
            "incomplete_count": 0,
        }


def _get_roadmap_phase(cwd: Path, phase_num: str) -> dict[str, Any] | None:
    """Extract phase details from ROADMAP.md."""
    roadmap_path = opc_paths(cwd)["roadmap"]
    if not roadmap_path.exists():
        return None

    content = safe_read(roadmap_path)
    escaped = re.escape(phase_num)
    header = re.search(rf"#{2,4}\s*Phase\s+{escaped}:\s*([^\n]+)", content, re.IGNORECASE)
    if not header:
        return None

    # Extract section
    start = header.start()
    rest = content[start + 1:]
    next_h = re.search(r"\n#{2,4}\s+Phase\s+\d", rest, re.IGNORECASE)
    section = content[start:start + 1 + next_h.start()] if next_h else content[start:]

    goal_m = re.search(r"\*\*Goal(?::\*\*|\*\*:)\s*([^\n]+)", section, re.IGNORECASE)
    req_m = re.search(r"\*\*Requirements\*\*:\s*([^\n]*)", section, re.IGNORECASE)

    return {
        "found": True,
        "phase_name": header.group(1).strip(),
        "goal": goal_m.group(1).strip() if goal_m else None,
        "requirements": req_m.group(1).strip() if req_m else None,
        "section": section.strip(),
    }


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_init_execute_phase(cwd: Path, phase_num: str, raw: bool) -> None:
    """All context needed for execute-phase workflow."""
    config = load_config(cwd)
    phase_info = _get_phase_info(cwd, phase_num)
    roadmap_phase = _get_roadmap_phase(cwd, phase_num)
    paths = opc_paths(cwd)

    # If phase not found on disk but exists in roadmap, create stub info
    if not phase_info["found"] and roadmap_phase and roadmap_phase["found"]:
        phase_info["phase_name"] = roadmap_phase["phase_name"]

    result = {
        # Config
        "commit_docs": config.get("commit_docs", True),
        "parallelization": config.get("parallelization", True),
        "code_review": config.get("workflow", {}).get("code_review", True),
        "verifier_enabled": config.get("workflow", {}).get("verifier", True),

        # Phase
        "phase_found": phase_info["found"],
        "phase_dir": phase_info["directory"],
        "phase_number": phase_info["phase_number"],
        "phase_name": phase_info.get("phase_name", ""),

        # Plans
        "plans": phase_info["plans"],
        "summaries": phase_info.get("summaries", []),
        "incomplete_plans": phase_info["incomplete_plans"],
        "plan_count": phase_info["plan_count"],
        "incomplete_count": phase_info["incomplete_count"],

        # Files
        "state_exists": paths["state"].exists(),
        "roadmap_exists": paths["roadmap"].exists(),
        "config_exists": paths["config"].exists(),
        "state_path": to_posix(paths["state"].relative_to(cwd)),
        "roadmap_path": to_posix(paths["roadmap"].relative_to(cwd)),
    }

    if roadmap_phase:
        result["roadmap_goal"] = roadmap_phase.get("goal")
        result["roadmap_requirements"] = roadmap_phase.get("requirements")

    output(_with_project_root(cwd, result), raw)


def cmd_init_plan_phase(cwd: Path, phase_num: str, raw: bool) -> None:
    """All context needed for plan-phase workflow."""
    config = load_config(cwd)
    phase_info = _get_phase_info(cwd, phase_num)
    roadmap_phase = _get_roadmap_phase(cwd, phase_num)
    paths = opc_paths(cwd)

    # Load requirements
    requirements_content = safe_read(paths["requirements"]) if paths["requirements"].exists() else ""

    result = {
        "commit_docs": config.get("commit_docs", True),
        "granularity": config.get("granularity", "standard"),
        "plan_check_enabled": config.get("workflow", {}).get("plan_check", True),
        "research_enabled": config.get("workflow", {}).get("research", True),

        "phase_found": phase_info["found"],
        "phase_dir": phase_info["directory"],
        "phase_number": phase_info["phase_number"],
        "phase_name": phase_info.get("phase_name", ""),
        "existing_plans": phase_info["plans"],

        "roadmap_exists": paths["roadmap"].exists(),
        "requirements_exists": paths["requirements"].exists(),
        "has_requirements": bool(requirements_content.strip()),
    }

    if roadmap_phase:
        result["roadmap_goal"] = roadmap_phase.get("goal")
        result["roadmap_requirements"] = roadmap_phase.get("requirements")
        result["roadmap_section"] = roadmap_phase.get("section")

    output(_with_project_root(cwd, result), raw)


def cmd_init_new_project(cwd: Path, raw: bool) -> None:
    """All context for new-project workflow."""
    from cli.core import CONFIG_DEFAULTS
    paths = opc_paths(cwd) if find_opc_exists(cwd) else {}

    result = {
        "opc_exists": bool(paths),
        "default_config": CONFIG_DEFAULTS,
        "cwd": to_posix(cwd),
        "timestamp": now_iso(),
    }
    output(_with_project_root(cwd, result), raw)


def cmd_init_quick(cwd: Path, description: str, raw: bool) -> None:
    """All context for quick workflow (small tasks without full phase cycle)."""
    config = load_config(cwd)
    paths = opc_paths(cwd)

    quick_dir = paths["opc"] / "quick"
    existing = sorted(quick_dir.glob("*.md")) if quick_dir.exists() else []

    result = {
        "description": description,
        "quick_dir": to_posix(quick_dir.relative_to(cwd)),
        "existing_quick_count": len(existing),
        "commit_docs": config.get("commit_docs", True),
        "state_exists": paths["state"].exists(),
        "timestamp": now_iso(),
    }
    output(_with_project_root(cwd, result), raw)


def cmd_init_resume(cwd: Path, raw: bool) -> None:
    """All context for resume workflow."""
    paths = opc_paths(cwd)
    state_content = safe_read(paths["state"])

    # Extract resume-relevant fields
    stop_point = extract_field(state_content, "Stop Point") or ""
    resume_file = extract_field(state_content, "Resume File") or ""
    current_focus = extract_field(state_content, "Current Focus") or ""
    status = extract_field(state_content, "Status") or ""
    last_session = extract_field(state_content, "Last Session") or ""

    # Load handoff
    handoff: dict[str, Any] = {}
    if paths["handoff"].exists():
        try:
            handoff = json.loads(paths["handoff"].read_text(encoding="utf-8"))
        except Exception:
            pass

    next_steps = handoff.get("nextSteps", [])
    resume_files = handoff.get("resumeFiles", [])

    result = {
        "status": status,
        "current_focus": current_focus,
        "stop_point": stop_point,
        "resume_file": resume_file,
        "last_session": last_session,
        "handoff_exists": paths["handoff"].exists(),
        "next_steps": next_steps,
        "resume_files": resume_files,
        "state_exists": paths["state"].exists(),
    }
    output(_with_project_root(cwd, result), raw)


def cmd_init_verify_work(cwd: Path, phase_num: str, raw: bool) -> None:
    """All context for verify-work workflow."""
    phase_info = _get_phase_info(cwd, phase_num)
    config = load_config(cwd)

    result = {
        "verifier_enabled": config.get("workflow", {}).get("verifier", True),
        "nyquist_enabled": config.get("workflow", {}).get("nyquist_validation", True),
        "phase_found": phase_info["found"],
        "phase_dir": phase_info["directory"],
        "phase_number": phase_info["phase_number"],
        "plans": phase_info["plans"],
        "summaries": phase_info.get("summaries", []),
        "incomplete_plans": phase_info["incomplete_plans"],
        "has_verification": phase_info.get("has_verification", False),
    }
    output(_with_project_root(cwd, result), raw)


def cmd_init_progress(cwd: Path, raw: bool) -> None:
    """All context for progress workflow."""
    paths = opc_paths(cwd)
    state_content = safe_read(paths["state"])

    # Count phases
    phase_dirs = list_phase_dirs(cwd)
    complete = 0
    for d in phase_dirs:
        verifications = list(d.glob("*VERIFICATION.md"))
        if verifications:
            v_content = safe_read(verifications[0])
            if re.search(r"status:\s*passed", v_content, re.IGNORECASE):
                complete += 1

    result = {
        "total_phases": len(phase_dirs),
        "complete_phases": complete,
        "current_focus": extract_field(state_content, "Current Focus") or "",
        "status": extract_field(state_content, "Status") or "",
        "phase": extract_field(state_content, "Phase") or "",
    }
    output(_with_project_root(cwd, result), raw)


def cmd_init_todos(cwd: Path, area: str | None, raw: bool) -> None:
    """All context for todo workflows."""
    from cli.state import cmd_list_todos
    cmd_list_todos(cwd, area, raw)


# ---------------------------------------------------------------------------
# Utility
# ---------------------------------------------------------------------------

def find_opc_exists(cwd: Path) -> bool:
    """Check if .opc/ exists without raising an error."""
    from cli.core import find_opc_dir
    return find_opc_dir(cwd) is not None
