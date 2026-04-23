#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from opc_common import find_opc_dir, read_json, read_text, write_console_text
from insights_helpers import (
    count_checklist_items,
    count_files,
    extract_first_heading,
    extract_metric,
    parse_git_info,
    parse_next_roadmap_task,
    parse_roadmap_progress,
    parse_risky_decisions,
    parse_state,
    parse_validation_debt,
    read_recent_sessions,
)


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("mode", nargs="?", choices=("dashboard", "stats"))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--json", action="store_true")
    return parser.parse_args(argv)


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
    from opc_quality import collect_project_quality_report

    quality_report = collect_project_quality_report(project_root, repair=False)
    quality_signals = quality_report["qualitySignals"]
    validation_debt = parse_validation_debt(
        state_text,
        git_info,
        warnings,
        extra_items=quality_report["validationDebt"],
    )

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
            "qualityFindings": quality_report["findings"],
            "qualitySummary": quality_report["summary"],
        },
        "validationDebt": validation_debt,
        "quality": quality_signals,
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
            "质量债务: "
            f"requirements={insights['quality']['requirementsCoverageDebt']} · regression={insights['quality']['regressionDebt']} · scope={insights['quality']['scopeDebt']} · traceability={insights['quality']['traceabilityDebt']} · schema={insights['quality']['schemaDriftDebt']}",
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


def build_stats_payload(insights: dict[str, Any]) -> dict[str, Any]:
    return {
        "project": {
            "name": insights["projectName"],
            "root": insights["projectRoot"],
            "focus": insights["state"]["currentFocus"],
            "status": insights["state"]["status"],
        },
        "progress": insights["progress"],
        "debt": insights["debt"],
        "validationDebt": insights["validationDebt"],
        "quality": insights["quality"],
        "business": insights["business"],
        "roadmap": insights["roadmap"]["rows"],
        "nextTask": insights["roadmap"]["nextTask"],
        "git": insights["git"],
        "warnings": insights["warnings"],
    }


def format_stats(insights: dict) -> str:
    return json.dumps(build_stats_payload(insights), ensure_ascii=True, indent=2)


def run_cli(default_mode: str) -> int:
    try:
        args = parse_args(sys.argv[1:])
        mode = args.mode or default_mode
        insights = collect_project_insights(Path(args.cwd))
        if args.json:
            payload: dict[str, Any] = insights if mode == "dashboard" else build_stats_payload(insights)
            write_console_text(json.dumps(payload, ensure_ascii=True, indent=2), stream=sys.stdout)
            return 0

        rendered = format_dashboard(insights) if mode == "dashboard" else format_stats(insights)
        write_console_text(rendered if mode == "stats" else f"{rendered}\n", stream=sys.stdout)
        return 0
    except Exception as exc:
        write_console_text(f"SuperOPC insights error: {exc}\n", stream=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli("dashboard"))
