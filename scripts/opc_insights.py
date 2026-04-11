#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable


@dataclass
class RoadmapRow:
    phase: str
    completed_plans: int
    total_plans: int
    status: str
    completed_date: str


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("mode", nargs="?", choices=("dashboard", "stats"))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


def find_opc_dir(start_dir: Path) -> Path | None:
    current = start_dir.resolve()

    if current.name == ".opc" and current.exists():
        return current

    for candidate in (current, *current.parents):
        opc_dir = candidate / ".opc"
        if opc_dir.exists() and opc_dir.is_dir():
            return opc_dir

    return None


def read_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


def read_json(file_path: Path) -> dict[str, Any]:
    try:
        payload = json.loads(file_path.read_text(encoding="utf-8"))
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def read_recent_sessions(sessions_dir: Path, limit: int = 5) -> list[dict[str, Any]]:
    if not sessions_dir.exists():
        return []

    sessions: list[dict[str, Any]] = []
    for session_file in sorted(
        sessions_dir.glob("session-*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        payload = read_json(session_file)
        if payload:
            payload["file"] = str(session_file)
            sessions.append(payload)
        if len(sessions) >= limit:
            break
    return sessions


def get_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#{{2,3}}\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^#{{2,3}}\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    return match.group(1).strip() if match else ""


def extract_first_heading(markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else "未命名项目"


def extract_inline_value(markdown: str, label: str) -> str:
    variants = [
        rf"\*\*{re.escape(label)}：\*\*\s*(.+)$",
        rf"\*\*{re.escape(label)}:\*\*\s*(.+)$",
        rf"{re.escape(label)}：\s*(.+)$",
        rf"{re.escape(label)}:\s*(.+)$",
    ]
    for variant in variants:
        match = re.search(variant, markdown, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def count_checklist_items(markdown: str) -> tuple[int, int]:
    total = len(re.findall(r"^- \[(?: |x)\]\s+", markdown, re.MULTILINE | re.IGNORECASE))
    completed = len(re.findall(r"^- \[x\]\s+", markdown, re.MULTILINE | re.IGNORECASE))
    return total, completed


def parse_roadmap_progress(roadmap_text: str) -> list[RoadmapRow]:
    section = get_section(roadmap_text, "进度")
    rows: list[RoadmapRow] = []

    if not section:
        return rows

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if (
            not line.startswith("|")
            or re.match(r"^(\|\-)+", line)
            or "阶段 | 已完成计划" in line
        ):
            continue

        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) < 4:
            continue

        plan_match = re.search(r"(\d+)\s*/\s*(\d+)", cells[1])
        rows.append(
            RoadmapRow(
                phase=cells[0],
                completed_plans=int(plan_match.group(1)) if plan_match else 0,
                total_plans=int(plan_match.group(2)) if plan_match else 0,
                status=cells[2],
                completed_date=cells[3],
            )
        )

    return rows


def parse_next_roadmap_task(roadmap_text: str) -> str:
    for line in roadmap_text.splitlines():
        if not re.match(r"^- \[ \]", line):
            continue
        if re.search(r"阶段\s+\d", line):
            continue
        return re.sub(r"\*\*", "", re.sub(r"^- \[ \]\s*", "", line)).strip()
    return "未在 ROADMAP.md 中找到未完成计划"


def extract_list_items(section_text: str) -> list[str]:
    if not section_text or "暂无" in section_text:
        return []

    items: list[str] = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^(?:-|\d+\.)\s+(.+)$", line)
        if match:
            items.append(match.group(1).strip())
    return items


def count_list_items(section_text: str) -> int:
    return len(extract_list_items(section_text))


def count_files(dir_path: Path) -> int:
    if not dir_path.exists():
        return 0

    total = 0
    for entry in dir_path.iterdir():
        if entry.name.startswith("."):
            continue
        total += count_files(entry) if entry.is_dir() else 1
    return total


def extract_metric(texts: Iterable[str], labels: Iterable[str]) -> str:
    for text in texts:
        if not text:
            continue
        for label in labels:
            variants = [
                rf"^\s*-\s*{re.escape(label)}\s*[:：]\s*(.+)$",
                rf"^\s*\*\*{re.escape(label)}\*\*\s*[:：]\s*(.+)$",
                rf"^\s*{re.escape(label)}\s*[:：]\s*(.+)$",
            ]
            for variant in variants:
                match = re.search(variant, text, re.MULTILINE)
                if match:
                    return match.group(1).strip()
    return "未记录"


def parse_risky_decisions(project_text: str) -> int:
    return sum(
        1
        for line in project_text.splitlines()
        if "|" in line and "⚠️" in line
    )


def parse_state(state_text: str) -> dict:
    phase_match = re.search(r"阶段：\[(.+?)\]\s*/\s*\[(.+?)\]\s*（(.+?)）", state_text)
    plan_match = re.search(r"计划：\[(.+?)\]\s*/\s*\[(.+?)\]\s*", state_text)
    progress_match = re.search(r"进度：.*?(\d+)%", state_text)
    todos = extract_list_items(get_section(state_text, "待办事项"))
    blockers = extract_list_items(get_section(state_text, "阻塞/关注"))

    return {
        "currentFocus": extract_inline_value(state_text, "当前焦点") or "未记录",
        "coreValue": extract_inline_value(state_text, "核心价值") or "未记录",
        "status": extract_inline_value(state_text, "状态") or "未记录",
        "recentActivity": extract_inline_value(state_text, "最近活动") or "未记录",
        "lastSession": extract_inline_value(state_text, "上次会话") or "未记录",
        "stopPoint": extract_inline_value(state_text, "停止于") or "未记录",
        "resumeFile": extract_inline_value(state_text, "恢复文件") or "未记录",
        "phase": (
            {
                "current": phase_match.group(1),
                "total": phase_match.group(2),
                "name": phase_match.group(3),
            }
            if phase_match
            else None
        ),
        "plan": (
            {
                "current": plan_match.group(1),
                "total": plan_match.group(2),
            }
            if plan_match
            else None
        ),
        "progressPercent": int(progress_match.group(1)) if progress_match else None,
        "blockerCount": len(blockers),
        "blockers": blockers,
        "todoCountFromState": len(todos),
        "todos": todos,
    }


def parse_git_info(project_root: Path) -> dict:
    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        branch = subprocess.check_output(
            ["git", "branch", "--show-current"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or "DETACHED"

        status_output = subprocess.check_output(
            ["git", "status", "--short"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        dirty_files = len(status_output.splitlines()) if status_output else 0

        last_commit = subprocess.check_output(
            ["git", "log", "-1", "--pretty=format:%h %cs %s"],
            cwd=project_root,
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip() or "无提交"

        return {
            "available": True,
            "branch": branch,
            "dirtyFiles": dirty_files,
            "lastCommit": last_commit,
        }
    except Exception:
        return {
            "available": False,
            "branch": "未知",
            "dirtyFiles": 0,
            "lastCommit": "不可用",
        }


def parse_validation_debt(state_text: str, git_info: dict, warnings: list[str]) -> list[str]:
    debt: list[str] = []

    validation_section = get_section(state_text, "验证欠债")
    debt.extend(extract_list_items(validation_section))

    if git_info.get("available") and git_info.get("dirtyFiles", 0) > 0:
        debt.append(f"未提交工作区变更：{git_info['dirtyFiles']} 个文件")

    debt.extend(warnings)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in debt:
        normalized = item.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped


def collect_project_insights(start_dir: Path) -> dict:
    opc_dir = find_opc_dir(start_dir)
    if opc_dir is None:
        raise RuntimeError("未找到 .opc/ 目录。请在项目根目录运行，或使用 --cwd 指向包含 .opc 的项目。")

    project_root = opc_dir.parent
    project_text = read_text(opc_dir / "PROJECT.md")
    requirements_text = read_text(opc_dir / "REQUIREMENTS.md")
    roadmap_text = read_text(opc_dir / "ROADMAP.md")
    state_text = read_text(opc_dir / "STATE.md")

    state = parse_state(state_text)
    roadmap_rows = parse_roadmap_progress(roadmap_text)
    requirements_total, requirements_completed = count_checklist_items(requirements_text)
    completed_phases = sum(1 for row in roadmap_rows if "完成" in row.status)
    total_plans = sum(row.total_plans for row in roadmap_rows)
    completed_plans = sum(row.completed_plans for row in roadmap_rows)
    todos_dir_count = count_files(opc_dir / "todos")
    warnings: list[str] = []
    handoff_file = opc_dir / "HANDOFF.json"
    handoff = read_json(handoff_file)
    sessions = read_recent_sessions(opc_dir / "sessions", limit=10)

    business_metric_sources = [
        state_text,
        project_text,
        read_text(opc_dir / "metrics.md"),
    ]
    business = {
        "mrr": extract_metric(business_metric_sources, ["MRR", "月经常性收入"]),
        "burn": extract_metric(business_metric_sources, ["Burn", "月支出", "Monthly Burn"]),
        "runway": extract_metric(business_metric_sources, ["Runway", "现金跑道", "Runway Months"]),
        "customers": extract_metric(
            business_metric_sources,
            ["Active Customers", "活跃客户", "Customers"],
        ),
    }

    if business["mrr"] == "未记录":
        warnings.append("未记录 MRR；可在 .opc/STATE.md 的“商业指标”部分补充。")
    if not project_text:
        warnings.append("缺少 .opc/PROJECT.md。")
    if not requirements_text:
        warnings.append("缺少 .opc/REQUIREMENTS.md。")
    if not roadmap_text:
        warnings.append("缺少 .opc/ROADMAP.md。")
    if not state_text:
        warnings.append("缺少 .opc/STATE.md。")

    git_info = parse_git_info(project_root)
    validation_debt = parse_validation_debt(state_text, git_info, warnings)

    return {
        "projectRoot": str(project_root),
        "opcDir": str(opc_dir),
        "projectName": extract_first_heading(project_text or roadmap_text or state_text),
        "state": state,
        "progress": {
            "phasesCompleted": completed_phases,
            "phasesTotal": len(roadmap_rows),
            "plansCompleted": completed_plans,
            "plansTotal": total_plans,
            "requirementsCompleted": requirements_completed,
            "requirementsTotal": requirements_total,
        },
        "roadmap": {
            "rows": [
                {
                    "phase": row.phase,
                    "completedPlans": row.completed_plans,
                    "totalPlans": row.total_plans,
                    "status": row.status,
                    "completedDate": row.completed_date,
                }
                for row in roadmap_rows
            ],
            "nextTask": parse_next_roadmap_task(roadmap_text),
        },
        "debt": {
            "blockers": state["blockerCount"],
            "blockerItems": state["blockers"],
            "todos": max(todos_dir_count, state["todoCountFromState"]),
            "todoItems": state["todos"],
            "riskyDecisions": parse_risky_decisions(project_text),
        },
        "validationDebt": validation_debt,
        "business": business,
        "git": git_info,
        "warnings": warnings,
        "handoff": handoff,
        "sessions": sessions,
        "files": {
            "project": str(opc_dir / "PROJECT.md"),
            "requirements": str(opc_dir / "REQUIREMENTS.md"),
            "roadmap": str(opc_dir / "ROADMAP.md"),
            "state": str(opc_dir / "STATE.md"),
            "handoff": str(opc_dir / "HANDOFF.json"),
            "sessionsDir": str(opc_dir / "sessions"),
            "auditLog": str(opc_dir / "audit.log"),
            "todosDir": str(opc_dir / "todos"),
        },
    }


def format_dashboard(insights: dict) -> str:
    progress = insights["progress"]
    state = insights["state"]
    business = insights["business"]
    debt = insights["debt"]
    git = insights["git"]

    phase_summary = (
        f"{progress['phasesCompleted']}/{progress['phasesTotal']}"
        if progress["phasesTotal"] > 0
        else "0/0"
    )
    plan_summary = (
        f"{progress['plansCompleted']}/{progress['plansTotal']}"
        if progress["plansTotal"] > 0
        else "0/0"
    )
    requirement_summary = (
        f"{progress['requirementsCompleted']}/{progress['requirementsTotal']}"
        if progress["requirementsTotal"] > 0
        else "0/0"
    )

    lines = [
        "SuperOPC Dashboard",
        f"项目: {insights['projectName']}",
        f"目录: {insights['projectRoot']}",
        f"当前焦点: {state['currentFocus']}",
        f"状态: {state['status']}",
    ]

    if state["phase"] or state["plan"]:
        phase = (
            f"阶段 {state['phase']['current']}/{state['phase']['total']}（{state['phase']['name']}）"
            if state["phase"]
            else "阶段未记录"
        )
        plan = (
            f"计划 {state['plan']['current']}/{state['plan']['total']}"
            if state["plan"]
            else "计划未记录"
        )
        lines.append(f"位置: {phase} · {plan}")

    if state["progressPercent"] is not None:
        lines.append(f"项目进度: {state['progressPercent']}%")

    lines.extend(
        [
            f"路线图: {phase_summary} 阶段完成 · {plan_summary} 计划完成 · {requirement_summary} 需求完成",
            "业务指标: "
            f"MRR={business['mrr']} · Burn={business['burn']} · Runway={business['runway']} · Customers={business['customers']}",
            f"项目债务: blockers={debt['blockers']} · todos={debt['todos']} · risky-decisions={debt['riskyDecisions']}",
            f"下一步: {insights['roadmap']['nextTask']}",
            f"最近活动: {state['recentActivity']}",
        ]
    )

    if git["available"]:
        lines.append(
            f"Git: branch={git['branch']} · dirty={git['dirtyFiles']} · last={git['lastCommit']}"
        )
    else:
        lines.append("Git: 不可用")

    if insights["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in insights["warnings"])

    return "\n".join(lines)


def format_stats(insights: dict) -> str:
    payload = {
        "project": {
            "name": insights["projectName"],
            "root": insights["projectRoot"],
            "focus": insights["state"]["currentFocus"],
            "status": insights["state"]["status"],
        },
        "progress": insights["progress"],
        "debt": insights["debt"],
        "validationDebt": insights["validationDebt"],
        "business": insights["business"],
        "roadmap": insights["roadmap"]["rows"],
        "nextTask": insights["roadmap"]["nextTask"],
        "git": insights["git"],
        "warnings": insights["warnings"],
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


def run_cli(default_mode: str) -> int:
    try:
        args = parse_args(sys.argv[1:])
        mode = args.mode or default_mode
        insights = collect_project_insights(Path(args.cwd))
        output = format_dashboard(insights) if mode == "dashboard" else format_stats(insights)
        sys.stdout.write(output if args.json or mode == "stats" else f"{output}\n")
        return 0
    except Exception as exc:
        sys.stderr.write(f"SuperOPC insights error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli("dashboard"))
