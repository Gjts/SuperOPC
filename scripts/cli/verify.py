"""
verify.py — Verification domain operations for opc-tools.

Provides: summary verification, plan structure checks, phase completeness,
consistency validation, and health checks with optional repair.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    exec_git,
    find_phase_dir,
    list_phase_dirs,
    normalize_phase_name,
    opc_dir,
    opc_paths,
    output,
    safe_read,
    to_posix,
)
from quality_project_checks import validate_project_checks


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def dispatch_verify(args: list[str], cwd: Path, raw: bool) -> None:
    """Route verify subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "summary":
        if not rest:
            error("summary path required")
        cmd_verify_summary(cwd, rest[0], raw)
    elif sub == "plan-structure":
        if not rest:
            error("plan path required")
        cmd_verify_plan_structure(cwd, rest[0], raw)
    elif sub == "phase-completeness":
        if not rest:
            error("phase number required")
        cmd_verify_phase_completeness(cwd, rest[0], raw)
    elif sub == "consistency":
        cmd_verify_consistency(cwd, raw)
    elif sub == "health":
        repair = "--repair" in rest
        cmd_verify_health(cwd, repair, raw)
    elif sub == "commits":
        cmd_verify_commits(cwd, rest, raw)
    elif sub == "references":
        if not rest:
            error("file path required")
        cmd_verify_references(cwd, rest[0], raw)
    else:
        error(f"Unknown verify subcommand: {sub}\nAvailable: summary, plan-structure, phase-completeness, consistency, health, commits, references")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_verify_summary(cwd: Path, summary_path: str, raw: bool) -> None:
    """Verify a SUMMARY.md file for completeness."""
    full_path = cwd / summary_path if not Path(summary_path).is_absolute() else Path(summary_path)
    errors: list[str] = []

    if not full_path.exists():
        output({
            "passed": False,
            "checks": {"summary_exists": False},
            "errors": ["SUMMARY.md not found"],
        }, raw, "failed")
        return

    content = full_path.read_text(encoding="utf-8")

    # Check 1: Spot-check files mentioned
    mentioned_files: set[str] = set()
    for pattern in [r"`([^`]+\.[a-zA-Z]+)`", r"(?:Created|Modified|Added):\s*`?([^\s`]+\.[a-zA-Z]+)`?"]:
        for m in re.finditer(pattern, content, re.IGNORECASE):
            fp = m.group(1)
            if fp and not fp.startswith("http") and "/" in fp:
                mentioned_files.add(fp)

    files_to_check = list(mentioned_files)[:3]
    missing = [f for f in files_to_check if not (cwd / f).exists()]

    # Check 2: Commit hashes
    commit_hashes = re.findall(r"\b[0-9a-f]{7,40}\b", content)
    commits_exist = False
    for h in commit_hashes[:3]:
        code, stdout, _ = exec_git(cwd, ["cat-file", "-t", h])
        if code == 0 and stdout == "commit":
            commits_exist = True
            break

    # Check 3: Self-check section
    self_check = "not_found"
    sc_match = re.search(r"##\s*(?:Self[- ]?Check|Verification|Quality Check)", content, re.IGNORECASE)
    if sc_match:
        section = content[sc_match.start():]
        if re.search(r"(?:fail|✗|❌|incomplete|blocked)", section, re.IGNORECASE):
            self_check = "failed"
        elif re.search(r"(?:pass|✓|✅|complete|succeeded)", section, re.IGNORECASE):
            self_check = "passed"

    if missing:
        errors.append("Missing files: " + ", ".join(missing))
    if not commits_exist and commit_hashes:
        errors.append("Referenced commit hashes not found")
    if self_check == "failed":
        errors.append("Self-check section indicates failure")

    passed = not missing and self_check != "failed"
    output({
        "passed": passed,
        "checks": {
            "summary_exists": True,
            "files_created": {"checked": len(files_to_check), "found": len(files_to_check) - len(missing), "missing": missing},
            "commits_exist": commits_exist,
            "self_check": self_check,
        },
        "errors": errors,
    }, raw, "passed" if passed else "failed")


def cmd_verify_plan_structure(cwd: Path, plan_path: str, raw: bool) -> None:
    """Check PLAN.md structure: has tasks, has frontmatter, etc."""
    full_path = cwd / plan_path if not Path(plan_path).is_absolute() else Path(plan_path)
    errors: list[str] = []

    if not full_path.exists():
        output({"valid": False, "errors": ["PLAN.md not found"]}, raw, "invalid")
        return

    content = full_path.read_text(encoding="utf-8")

    # Check frontmatter
    has_frontmatter = content.startswith("---")
    has_opc_plan_block = bool(re.search(r"<opc-plan>[\s\S]*?</opc-plan>", content, re.IGNORECASE))

    # Check for task markers
    task_pattern = re.compile(r"(?:^|\n)#+\s*(?:Task|Step|任务)\s+\d", re.IGNORECASE)
    checkbox_pattern = re.compile(r"- \[[ x]\]")
    tasks_found = bool(task_pattern.search(content)) or len(checkbox_pattern.findall(content)) >= 2

    # Check for goal/objective
    has_goal = bool(re.search(r"\*\*(?:Goal|Objective|目标)(?::\*\*|\*\*:)", content, re.IGNORECASE))
    has_plan_check = bool(re.search(r"^##\s+OPC Plan Check\b", content, re.IGNORECASE | re.MULTILINE))
    has_assumptions_analysis = bool(re.search(r"^##\s+OPC Assumptions Analysis\b", content, re.IGNORECASE | re.MULTILINE))

    gate_block = re.search(
        r"^##\s+OPC Pre-flight Gate\b(?P<body>[\s\S]*?)(?:\n##\s+|\Z)",
        content,
        re.IGNORECASE | re.MULTILINE,
    )
    gate_values: dict[str, str | None] = {
        "plan-check": None,
        "assumptions": None,
        "ready-for-build": None,
    }
    if gate_block:
        body = gate_block.group("body")
        for key in gate_values:
            match = re.search(rf"^-\s*{re.escape(key)}:\s*(.+)$", body, re.IGNORECASE | re.MULTILINE)
            if match:
                gate_values[key] = match.group(1).strip()

    if not tasks_found:
        errors.append("No task markers found (expected ## Task N or - [ ] checkboxes)")
    if not has_goal:
        errors.append("No Goal/Objective section found")
    if not has_opc_plan_block:
        errors.append("No <opc-plan> block found")
    if not has_plan_check:
        errors.append("Missing ## OPC Plan Check section")
    if not has_assumptions_analysis:
        errors.append("Missing ## OPC Assumptions Analysis section")
    if gate_block is None:
        errors.append("Missing ## OPC Pre-flight Gate section")
    else:
        if (gate_values["plan-check"] or "").upper() != "APPROVED":
            errors.append("Pre-flight gate requires plan-check: APPROVED")
        if (gate_values["assumptions"] or "").upper() != "PASS":
            errors.append("Pre-flight gate requires assumptions: PASS")
        if (gate_values["ready-for-build"] or "").lower() != "true":
            errors.append("Pre-flight gate requires ready-for-build: true")

    valid = not errors
    output({
        "valid": valid,
        "has_frontmatter": has_frontmatter,
        "has_opc_plan_block": has_opc_plan_block,
        "tasks_found": tasks_found,
        "has_goal": has_goal,
        "has_plan_check": has_plan_check,
        "has_assumptions_analysis": has_assumptions_analysis,
        "preflight_gate": gate_values,
        "errors": errors,
    }, raw, "valid" if valid else "invalid")


def cmd_verify_phase_completeness(cwd: Path, phase_num: str, raw: bool) -> None:
    """Check that all plans in a phase have corresponding summaries."""
    phase_dir = find_phase_dir(cwd, phase_num)
    if not phase_dir:
        error(f"Phase {phase_num} directory not found")

    plans = sorted(f.name for f in phase_dir.glob("*PLAN.md"))
    summaries = sorted(f.name for f in phase_dir.glob("*SUMMARY.md"))

    # Match plans to summaries
    incomplete: list[str] = []
    for plan in plans:
        expected_summary = plan.replace("-PLAN.md", "-SUMMARY.md").replace("PLAN.md", "SUMMARY.md")
        if expected_summary not in summaries:
            incomplete.append(plan)

    complete = not incomplete
    output({
        "complete": complete,
        "phase": phase_num,
        "plans": len(plans),
        "summaries": len(summaries),
        "incomplete_plans": incomplete,
    }, raw, "complete" if complete else f"incomplete ({len(incomplete)} plans missing summaries)")


def cmd_verify_consistency(cwd: Path, raw: bool) -> None:
    """Check phase numbering and disk/roadmap sync."""
    issues: list[str] = []

    # Check .opc/ exists
    paths = opc_paths(cwd)
    if not paths["opc"].exists():
        output({"consistent": False, "issues": [".opc/ directory not found"]}, raw, "inconsistent")
        return

    # Check required files
    for name in ["project", "requirements", "roadmap", "state", "config"]:
        if not paths[name].exists():
            issues.append(f"Missing: {paths[name].name}")

    # Check phase directory numbering
    dirs = list_phase_dirs(cwd)
    seen_numbers: set[str] = set()
    for d in dirs:
        match = re.match(r"(\d+(?:\.\d+)?)", d.name)
        if match:
            num = normalize_phase_name(match.group(1))
            if num in seen_numbers:
                issues.append(f"Duplicate phase number: {num}")
            seen_numbers.add(num)

    # Check roadmap phases exist on disk
    if paths["roadmap"].exists():
        content = safe_read(paths["roadmap"])
        for m in re.finditer(r"#{2,4}\s*Phase\s+(\d+(?:\.\d+)?):", content, re.IGNORECASE):
            num = normalize_phase_name(m.group(1))
            if not find_phase_dir(cwd, num):
                issues.append(f"Roadmap phase {num} has no directory on disk")

    consistent = not issues
    output({"consistent": consistent, "issues": issues}, raw, "consistent" if consistent else "inconsistent")


def cmd_verify_health(cwd: Path, repair: bool, raw: bool) -> None:
    """Check .opc/ integrity, optionally repair missing structures."""
    report = validate_project_checks(cwd, repair)
    issues: list[str] = []
    warnings: list[str] = []
    for check in report["checks"]:
        message = f"{check['id']}: {check['message']}"
        if check["status"] == "fail":
            issues.append(message)
        elif check["status"] == "warn":
            warnings.append(message)

    healthy = report["summary"]["fail"] == 0
    output({
        "healthy": healthy,
        "issues": issues,
        "warnings": warnings,
        "repaired": report["repairs"],
    }, raw, "healthy" if healthy else f"unhealthy ({len(issues)} issues)")


def cmd_verify_commits(cwd: Path, hashes: list[str], raw: bool) -> None:
    """Batch verify commit hashes exist in git."""
    results: list[dict[str, Any]] = []
    for h in hashes:
        code, stdout, _ = exec_git(cwd, ["cat-file", "-t", h])
        results.append({
            "hash": h,
            "exists": code == 0 and stdout == "commit",
            "type": stdout if code == 0 else None,
        })

    all_exist = all(r["exists"] for r in results)
    output({"all_exist": all_exist, "results": results}, raw, "true" if all_exist else "false")


def cmd_verify_references(cwd: Path, file_path: str, raw: bool) -> None:
    """Check @-references and file paths in a document resolve correctly."""
    full_path = cwd / file_path if not Path(file_path).is_absolute() else Path(file_path)
    if not full_path.exists():
        error(f"File not found: {file_path}")

    content = full_path.read_text(encoding="utf-8")
    # Find file references: `path/to/file.ext` patterns
    refs = re.findall(r"`([^`]+/[^`]+\.[a-zA-Z]+)`", content)
    missing: list[str] = []
    checked: list[str] = []

    for ref in refs:
        if ref.startswith("http"):
            continue
        checked.append(ref)
        if not (cwd / ref).exists():
            missing.append(ref)

    output({
        "checked": len(checked),
        "missing": missing,
        "all_resolved": not missing,
    }, raw, "all_resolved" if not missing else f"{len(missing)} missing")
