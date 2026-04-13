#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parent / "engine"
if str(ENGINE_DIR) not in sys.path:
    sys.path.insert(0, str(ENGINE_DIR))

from opc_insights import collect_project_insights

# v2 engine imports — graceful fallback if engine modules are unavailable
try:
    from event_bus import EventBus, get_event_bus
    from state_engine import StateEngine, get_state_engine
    from decision_engine import DecisionEngine, ActionType

    _V2_AVAILABLE = True
except ImportError:
    _V2_AVAILABLE = False


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("mode", nargs="?", choices=("progress", "report", "pause", "resume", "next", "autonomous"))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--note", default="")
    parser.add_argument("--stop-point", default="")
    parser.add_argument("--from", dest="from_index", type=int)
    parser.add_argument("--to", dest="to_index", type=int)
    parser.add_argument("--only", type=int)
    parser.add_argument("--interactive", action="store_true")
    return parser.parse_args(argv)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def read_json(file_path: Path) -> dict[str, Any]:
    try:
        data = json.loads(file_path.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def write_json(file_path: Path, payload: dict[str, Any]) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def read_recent_audit_lines(audit_log: Path, limit: int = 10) -> list[str]:
    try:
        lines = audit_log.read_text(encoding="utf-8").splitlines()
        return lines[-limit:]
    except OSError:
        return []


def _get_v2_bus(project_root: Path | None = None) -> Any:
    """Get the v2 event bus if available, None otherwise."""
    if not _V2_AVAILABLE:
        return None
    try:
        opc_dir = _find_opc_dir(project_root or Path.cwd())
        journal_dir = opc_dir / "events" if opc_dir else None
        if journal_dir:
            journal_dir.mkdir(parents=True, exist_ok=True)
        return get_event_bus(journal_dir=journal_dir)
    except Exception:
        return None


def _find_opc_dir(start: Path) -> Path | None:
    """Walk up from start to find .opc/ directory."""
    for candidate in [start] + list(start.parents):
        opc = candidate / ".opc"
        if opc.is_dir():
            return opc
    return None


def _v2_decision_recommendation(insights: dict[str, Any]) -> dict[str, str] | None:
    """Try to get a recommendation from the v2 decision engine."""
    if not _V2_AVAILABLE:
        return None
    try:
        project_root = Path(insights.get("projectRoot", "."))
        opc_dir = _find_opc_dir(project_root)
        if not opc_dir:
            return None

        bus = get_event_bus()
        se = get_state_engine(opc_dir, bus)
        se.load()

        debt = insights.get("debt", {})
        blocker_items = debt.get("blockerItems", [])
        if blocker_items and not se.state.blockers:
            for b in blocker_items:
                se.state.blockers.append(b)

        de = DecisionEngine(se, bus)

        context: dict[str, Any] = {}
        handoff_file = opc_dir / "HANDOFF.json"
        if handoff_file.exists():
            context["handoff_exists"] = True
        if insights.get("validationDebt"):
            context["quality_violations"] = insights["validationDebt"]

        decision = de.decide(context)
        return {
            "command": decision.command,
            "reason": decision.reason,
            "zone": decision.zone.value,
            "confidence": str(decision.confidence),
            "source": "v2_decision_engine",
        }
    except Exception:
        return None


def recommendation_from_insights(insights: dict[str, Any]) -> dict[str, str]:
    v2_result = _v2_decision_recommendation(insights)
    if v2_result:
        return v2_result

    state = insights["state"]
    roadmap = insights["roadmap"]
    debt = insights["debt"]
    validation_debt = insights["validationDebt"]

    status = state.get("status", "未记录")
    next_task = roadmap.get("nextTask", "未在 ROADMAP.md 中找到未完成计划")

    if debt["blockers"] > 0:
        return {
            "command": "/opc-discuss",
            "reason": f"当前存在 {debt['blockers']} 个阻塞，先澄清阻塞再推进执行。",
        }
    if validation_debt:
        return {
            "command": "/opc-progress",
            "reason": "当前仍有验证欠债，先确认未验证事项，再继续推进。",
        }
    if status in {"准备规划", "规划中"}:
        return {
            "command": "/opc-plan",
            "reason": "当前处于规划前后语境，下一步应收敛方案并生成计划。",
        }
    if status in {"准备执行", "执行中"}:
        return {
            "command": "/opc-build",
            "reason": "当前状态已经进入执行路径，下一步应落实计划或继续实现。",
        }
    if status == "阶段完成":
        return {
            "command": "/opc-review",
            "reason": "当前阶段已完成，优先做审查与验证，再决定 ship。",
        }
    if next_task and next_task != "未在 ROADMAP.md 中找到未完成计划":
        return {
            "command": "/opc-next",
            "reason": f"路线图中的下一个未完成项是：{next_task}",
        }
    return {
        "command": "/opc-discuss",
        "reason": "缺少足够的状态信号，先通过讨论模式澄清当前目标。",
    }


def extract_handoff_next_steps(handoff: dict[str, Any]) -> list[str]:
    next_steps = handoff.get("nextSteps")
    if isinstance(next_steps, list):
        return [str(item).strip() for item in next_steps if str(item).strip()]

    legacy_next_step = handoff.get("nextStep")
    if isinstance(legacy_next_step, str) and legacy_next_step.strip():
        return [legacy_next_step.strip()]
    return []


def first_resume_file(handoff: dict[str, Any], fallback: str) -> str:
    resume_files = handoff.get("resumeFiles")
    if isinstance(resume_files, list):
        for item in resume_files:
            value = str(item).strip()
            if value:
                return value
    return fallback


def path_exists_for_resume(project_root: Path, candidate: str) -> bool:
    if not candidate or candidate == "未记录":
        return False

    candidate_path = Path(candidate)
    if candidate_path.is_absolute():
        return candidate_path.exists()
    return (project_root / candidate).exists()


def collect_progress_snapshot(start_dir: Path) -> dict[str, Any]:
    insights = collect_project_insights(start_dir)
    recommendation = recommendation_from_insights(insights)
    latest_session = insights["sessions"][0] if insights["sessions"] else {}
    return {
        "project": {
            "name": insights["projectName"],
            "root": insights["projectRoot"],
        },
        "position": {
            "focus": insights["state"]["currentFocus"],
            "status": insights["state"]["status"],
            "recentActivity": insights["state"]["recentActivity"],
            "phase": insights["state"]["phase"],
            "plan": insights["state"]["plan"],
            "lastSession": insights["state"]["lastSession"],
            "stopPoint": insights["state"]["stopPoint"],
            "resumeFile": insights["state"]["resumeFile"],
        },
        "completion": insights["progress"],
        "debt": insights["debt"],
        "validationDebt": insights["validationDebt"],
        "quality": insights["quality"],
        "nextTask": insights["roadmap"]["nextTask"],
        "recommendation": recommendation,
        "warnings": insights["warnings"],
        "handoff": insights["handoff"],
        "latestSession": latest_session,
        "files": insights["files"],
    }


def format_progress(snapshot: dict[str, Any]) -> str:
    position = snapshot["position"]
    completion = snapshot["completion"]
    debt = snapshot["debt"]
    recommendation = snapshot["recommendation"]
    latest_session = snapshot["latestSession"]

    lines = [
        "SuperOPC Progress",
        f"项目: {snapshot['project']['name']}",
        f"目录: {snapshot['project']['root']}",
        f"当前焦点: {position['focus']}",
        f"状态: {position['status']}",
    ]

    if position["phase"] or position["plan"]:
        phase = (
            f"阶段 {position['phase']['current']}/{position['phase']['total']}（{position['phase']['name']}）"
            if position["phase"]
            else "阶段未记录"
        )
        plan = (
            f"计划 {position['plan']['current']}/{position['plan']['total']}"
            if position["plan"]
            else "计划未记录"
        )
        lines.append(f"位置: {phase} · {plan}")

    lines.extend(
        [
            f"完成度: phases={completion['phasesCompleted']}/{completion['phasesTotal']} · plans={completion['plansCompleted']}/{completion['plansTotal']} · requirements={completion['requirementsCompleted']}/{completion['requirementsTotal']}",
            f"项目债务: blockers={debt['blockers']} · todos={debt['todos']} · risky-decisions={debt['riskyDecisions']}",
            "质量债务: "
            f"requirements={snapshot['quality']['requirementsCoverageDebt']} · regression={snapshot['quality']['regressionDebt']} · scope={snapshot['quality']['scopeDebt']} · traceability={snapshot['quality']['traceabilityDebt']} · schema={snapshot['quality']['schemaDriftDebt']}",
            f"下一步: {snapshot['nextTask']}",
            f"建议命令: {recommendation['command']} — {recommendation['reason']}",
            f"最近活动: {position['recentActivity']}",
            f"上次会话: {position['lastSession']}",
            f"停止于: {position['stopPoint']}",
            f"恢复文件: {position['resumeFile']}",
        ]
    )

    if debt["blockerItems"]:
        lines.append("阻塞项:")
        lines.extend(f"- {item}" for item in debt["blockerItems"])

    if debt["todoItems"]:
        lines.append("待办项:")
        lines.extend(f"- {item}" for item in debt["todoItems"])

    if snapshot["validationDebt"]:
        lines.append("验证欠债:")
        lines.extend(f"- {item}" for item in snapshot["validationDebt"])

    if latest_session:
        lines.append(
            f"最近会话记录: {latest_session.get('timestamp', '未记录')} · tool={latest_session.get('tool_name', 'unknown')} · session={latest_session.get('session_id', 'unknown')}"
        )

    if snapshot["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in snapshot["warnings"])

    return "\n".join(lines)


def build_handoff_payload(start_dir: Path, note: str = "", stop_point: str = "") -> dict[str, Any]:
    snapshot = collect_progress_snapshot(start_dir)
    project_root = snapshot["project"]["root"]
    primary_next_step = snapshot["nextTask"]
    secondary_next_step = snapshot["recommendation"]["reason"]

    next_steps = [
        item
        for item in [primary_next_step, secondary_next_step]
        if item and item != "未在 ROADMAP.md 中找到未完成计划"
    ]
    resume_files = [
        item
        for item in [snapshot["position"]["resumeFile"], ".opc/STATE.md", ".opc/ROADMAP.md"]
        if item and item != "未记录"
    ]

    deduped_resume_files: list[str] = []
    seen_resume: set[str] = set()
    for item in resume_files:
        if item not in seen_resume:
            deduped_resume_files.append(item)
            seen_resume.add(item)

    return {
        "version": "0.8.0",
        "updatedAt": now_iso(),
        "project": {
            "name": snapshot["project"]["name"],
            "root": project_root,
        },
        "session": {
            "id": snapshot["latestSession"].get("session_id", "") if snapshot["latestSession"] else "",
            "mode": snapshot["position"]["status"],
            "source": "manual-pause",
        },
        "location": {
            "phase": (
                f"{snapshot['position']['phase']['current']}/{snapshot['position']['phase']['total']}"
                if snapshot["position"]["phase"]
                else ""
            ),
            "plan": (
                f"{snapshot['position']['plan']['current']}/{snapshot['position']['plan']['total']}"
                if snapshot["position"]["plan"]
                else ""
            ),
            "status": snapshot["position"]["status"],
        },
        "summary": {
            "completed": snapshot["position"]["recentActivity"],
            "stopPoint": stop_point.strip() or snapshot["position"]["stopPoint"],
            "reasonForPause": note.strip() or "会话检查点",
        },
        "nextSteps": next_steps[:3],
        "blockers": snapshot["debt"]["blockerItems"],
        "validationDebt": snapshot["validationDebt"],
        "resumeFiles": deduped_resume_files,
        "notes": [note.strip()] if note.strip() else [],
    }


def _replace_inline_value(text: str, label: str, value: str, colon: str = "：") -> str:
    pattern = re.compile(rf"({label}{re.escape(colon)}\s*).+$", re.MULTILINE)
    return pattern.sub(lambda match: f"{match.group(1)}{value}", text, count=1)


def update_state_continuity(state_file: Path, *, timestamp: str, stop_point: str, resume_file: str, recent_activity: str) -> None:
    try:
        content = state_file.read_text(encoding="utf-8")
    except OSError:
        return

    replacements = {
        "上次会话": timestamp,
        "停止于": stop_point or "已记录到 HANDOFF.json",
        "恢复文件": resume_file or "无",
        "最近活动": recent_activity,
    }

    for label, value in replacements.items():
        marker = f"{label}："
        if marker in content:
            content = _replace_inline_value(content, label, value)
            continue
        alt_marker = f"{label}:"
        if alt_marker in content:
            content = _replace_inline_value(content, label, value, colon=":")

    state_file.write_text(content, encoding="utf-8")


def pause_project(start_dir: Path, note: str = "", stop_point: str = "") -> dict[str, Any]:
    snapshot = collect_progress_snapshot(start_dir)
    opc_dir = Path(snapshot["files"]["state"]).parent
    handoff_file = opc_dir / "HANDOFF.json"
    payload = build_handoff_payload(start_dir, note=note, stop_point=stop_point)
    write_json(handoff_file, payload)
    update_state_continuity(
        Path(snapshot["files"]["state"]),
        timestamp=payload["updatedAt"],
        stop_point=payload["summary"]["stopPoint"],
        resume_file=first_resume_file(payload, str(handoff_file)),
        recent_activity=f"{payload['updatedAt']} — 已写入 HANDOFF.json",
    )
    payload["handoffFile"] = str(handoff_file)

    bus = _get_v2_bus(start_dir)
    if bus:
        bus.publish("session.pause", {
            "project": payload.get("project", {}).get("name", ""),
            "stop_point": stop_point or payload["summary"].get("stopPoint", ""),
            "note": note,
        }, source="opc_workflow")

    return payload


def resume_project(start_dir: Path) -> dict[str, Any]:
    snapshot = collect_progress_snapshot(start_dir)
    handoff = read_json(Path(snapshot["files"]["handoff"]))
    resume_file = first_resume_file(handoff, snapshot["position"]["resumeFile"])
    project_root = Path(snapshot["project"]["root"])
    conflicts: list[str] = []

    handoff_status = handoff.get("location", {}).get("status", "") if isinstance(handoff.get("location"), dict) else ""
    if handoff_status and handoff_status != snapshot["position"]["status"]:
        conflicts.append(f"handoff 状态为“{handoff_status}”，但 STATE.md 状态为“{snapshot['position']['status']}”。")

    if resume_file and not path_exists_for_resume(project_root, resume_file):
        conflicts.append(f"恢复文件不存在：{resume_file}")

    resume_timestamp = now_iso()
    stop_point = handoff.get("summary", {}).get("stopPoint", "") if isinstance(handoff.get("summary"), dict) else ""
    recent_activity = f"{resume_timestamp} — 已恢复会话上下文"
    if handoff:
        recent_activity = f"{resume_timestamp} — 已从 HANDOFF.json 恢复上下文"

    update_state_continuity(
        Path(snapshot["files"]["state"]),
        timestamp=resume_timestamp,
        stop_point=stop_point or snapshot["position"]["stopPoint"],
        resume_file=resume_file,
        recent_activity=recent_activity,
    )

    refreshed_snapshot = collect_progress_snapshot(start_dir)
    result = {
        "project": refreshed_snapshot["project"],
        "handoff": handoff,
        "progress": refreshed_snapshot,
        "resumeFile": resume_file,
        "conflicts": conflicts,
        "recommendedAction": recommendation_from_insights(collect_project_insights(start_dir)),
    }

    bus = _get_v2_bus(start_dir)
    if bus:
        bus.publish("session.resume", {
            "project": result["project"].get("name", ""),
            "conflicts": len(conflicts),
            "recommendation": result["recommendedAction"].get("command", ""),
        }, source="opc_workflow")

    return result


def format_resume(payload: dict[str, Any]) -> str:
    handoff = payload["handoff"]
    progress = payload["progress"]
    recommendation = payload["recommendedAction"]
    next_steps = extract_handoff_next_steps(handoff)

    lines = [
        "SuperOPC Resume",
        f"项目: {payload['project']['name']}",
        f"目录: {payload['project']['root']}",
    ]

    if handoff:
        lines.extend(
            [
                f"上次保存: {handoff.get('updatedAt', '未记录')}",
                f"停止点: {handoff.get('summary', {}).get('stopPoint', '未记录')}",
                f"暂停原因: {handoff.get('summary', {}).get('reasonForPause', '未记录')}",
                f"恢复文件: {payload['resumeFile'] or '未记录'}",
            ]
        )
        if next_steps:
            lines.append(f"主下一步: {next_steps[0]}")
    else:
        lines.append("未找到 HANDOFF.json，将基于当前 STATE.md 恢复。")

    if payload["conflicts"]:
        lines.append("冲突/警告:")
        lines.extend(f"- {item}" for item in payload["conflicts"])

    lines.append(f"建议恢复命令: {recommendation['command']} — {recommendation['reason']}")
    lines.append(f"当前焦点: {progress['position']['focus']}")
    return "\n".join(lines)


def collect_session_report(start_dir: Path) -> dict[str, Any]:
    insights = collect_project_insights(start_dir)
    opc_dir = Path(insights["opcDir"])
    handoff = insights["handoff"]
    sessions = insights["sessions"]
    audit_lines = read_recent_audit_lines(opc_dir / "audit.log")
    recommendation = recommendation_from_insights(insights)
    return {
        "project": {
            "name": insights["projectName"],
            "root": insights["projectRoot"],
        },
        "state": insights["state"],
        "progress": insights["progress"],
        "debt": insights["debt"],
        "validationDebt": insights["validationDebt"],
        "quality": insights["quality"],
        "handoff": handoff,
        "recentSessions": sessions,
        "recentAudit": audit_lines,
        "recommendation": recommendation,
        "warnings": insights["warnings"],
    }


def format_session_report(report: dict[str, Any]) -> str:
    lines = [
        "SuperOPC Session Report",
        f"项目: {report['project']['name']}",
        f"目录: {report['project']['root']}",
        f"当前状态: {report['state']['status']}",
        f"当前焦点: {report['state']['currentFocus']}",
        f"进度: phases={report['progress']['phasesCompleted']}/{report['progress']['phasesTotal']} · plans={report['progress']['plansCompleted']}/{report['progress']['plansTotal']} · requirements={report['progress']['requirementsCompleted']}/{report['progress']['requirementsTotal']}",
        f"债务: blockers={report['debt']['blockers']} · todos={report['debt']['todos']} · risky-decisions={report['debt']['riskyDecisions']}",
        "质量债务: "
        f"requirements={report['quality']['requirementsCoverageDebt']} · regression={report['quality']['regressionDebt']} · scope={report['quality']['scopeDebt']} · traceability={report['quality']['traceabilityDebt']} · schema={report['quality']['schemaDriftDebt']}",
        f"建议命令: {report['recommendation']['command']} — {report['recommendation']['reason']}",
    ]

    if report["validationDebt"]:
        lines.append("验证欠债:")
        lines.extend(f"- {item}" for item in report["validationDebt"])

    if report["handoff"]:
        next_steps = extract_handoff_next_steps(report["handoff"])
        lines.append("")
        lines.append("Latest handoff:")
        lines.append(f"- updatedAt: {report['handoff'].get('updatedAt', '未记录')}")
        lines.append(f"- stopPoint: {report['handoff'].get('summary', {}).get('stopPoint', '未记录')}")
        lines.append(f"- nextStep: {next_steps[0] if next_steps else '未记录'}")

    if report["recentSessions"]:
        lines.append("")
        lines.append("Recent sessions:")
        for session in report["recentSessions"]:
            lines.append(
                f"- {session.get('timestamp', '未记录')} · tool={session.get('tool_name', 'unknown')} · session={session.get('session_id', 'unknown')}"
            )

    if report["recentAudit"]:
        lines.append("")
        lines.append("Recent audit commands:")
        lines.extend(f"- {line}" for line in report["recentAudit"])

    if report["warnings"]:
        lines.append("")
        lines.append("Warnings:")
        lines.extend(f"- {warning}" for warning in report["warnings"])

    return "\n".join(lines)


def _derive_autonomous_window(position: dict[str, Any], *, from_index: int | None, to_index: int | None, only: int | None) -> dict[str, int | None]:
    current_phase = None
    phase = position.get("phase")
    if isinstance(phase, dict):
        try:
            current_phase = int(str(phase.get("current", "")).strip())
        except ValueError:
            current_phase = None

    if only is not None:
        return {
            "from": only,
            "to": only,
            "only": only,
            "current": current_phase,
        }

    start = from_index if from_index is not None else current_phase
    end = to_index if to_index is not None else start
    return {
        "from": start,
        "to": end,
        "only": None,
        "current": current_phase,
    }


def collect_autonomous_plan(
    start_dir: Path,
    *,
    from_index: int | None = None,
    to_index: int | None = None,
    only: int | None = None,
    interactive: bool = False,
) -> dict[str, Any]:
    snapshot = collect_progress_snapshot(start_dir)
    state = snapshot["position"]
    debt = snapshot["debt"]
    validation_debt = snapshot["validationDebt"]
    window = _derive_autonomous_window(state, from_index=from_index, to_index=to_index, only=only)

    blockers = debt["blockerItems"]
    recommendation_command = "/opc-autonomous"
    recommendation_reason = "当前状态适合在明确边界内连续推进。"
    mode = "autonomous"

    if blockers:
        recommendation_command = "/opc-discuss"
        recommendation_reason = "当前仍有 blocker，先解除阻塞再进入自主推进。"
        mode = "blocked"
    elif validation_debt:
        recommendation_command = "/opc-progress"
        recommendation_reason = "当前存在验证欠债，先确认未验证事项，再决定是否继续自主推进。"
        mode = "needs-validation"
    elif interactive:
        recommendation_command = "/opc-autonomous --interactive"
        recommendation_reason = "当前将保留人工检查点，在关键决策或人工验证处停下。"
        mode = "interactive"

    phase = state.get("phase")
    plan = state.get("plan")
    current_phase = phase.get("name", "未记录阶段") if isinstance(phase, dict) else "未记录阶段"
    current_plan = (
        f"{plan.get('current', '未记录')}/{plan.get('total', '未记录')}"
        if isinstance(plan, dict)
        else "未记录"
    )
    scope_label = (
        f"阶段 {window['only']}"
        if window["only"] is not None
        else f"阶段 {window['from'] or '当前'} → {window['to'] or window['from'] or '当前'}"
    )

    steps = [
        f"确认当前位置：{current_phase} · 当前计划={current_plan} · 目标范围={scope_label} · 状态={state['status']}",
        "优先读取 .opc/STATE.md、.opc/ROADMAP.md 与当前恢复文件，确认边界没有漂移。",
        "根据当前位置优先路由到 /opc-next 推荐的主动作，再进入 /opc-plan、/opc-fast、/opc-quick、/opc-build 或 /opc-review。",
        "如果所执行计划包含 checkpoint:decision 或 checkpoint:human-verify，则切换到交互式停点。",
        "逐项推进当前窗口内可自动执行的工作，并在每一项后记录最小验证结果。",
        "若出现新 blocker、范围分歧或验证欠债扩大，立即停下并退回 /opc-discuss 或 /opc-progress。",
    ]

    if mode == "blocked":
        steps = [
            "先列清 blocker 与缺失信息。",
            "通过 /opc-discuss 收敛决策，再重新进入 /opc-autonomous。",
        ]
    elif mode == "needs-validation":
        steps = [
            "先核对 validation debt 中哪些会影响继续执行。",
            "通过 /opc-progress 明确已验证/未验证边界。",
            "验证完成后，再重新进入 /opc-autonomous。",
        ]

    return {
        "project": snapshot["project"],
        "position": state,
        "window": window,
        "mode": mode,
        "interactive": interactive,
        "blockers": blockers,
        "validationDebt": validation_debt,
        "recommendation": {
            "command": recommendation_command,
            "reason": recommendation_reason,
        },
        "nextTask": snapshot["nextTask"],
        "resumeFiles": [
            item
            for item in [snapshot["handoff"].get("resumeFiles", [None])[0] if isinstance(snapshot["handoff"].get("resumeFiles"), list) and snapshot["handoff"].get("resumeFiles") else None, state.get("resumeFile"), ".opc/ROADMAP.md"]
            if item and item != "未记录"
        ],
        "steps": steps,
        "warnings": snapshot["warnings"],
    }


def format_autonomous_plan(payload: dict[str, Any]) -> str:
    window = payload["window"]
    lines = [
        "SuperOPC Autonomous",
        f"项目: {payload['project']['name']}",
        f"目录: {payload['project']['root']}",
        f"状态: {payload['position']['status']}",
        f"当前焦点: {payload['position']['focus']}",
        f"执行模式: {payload['mode']}",
    ]

    if window["only"] is not None:
        lines.append(f"目标计划: only={window['only']}")
    else:
        lines.append(f"目标窗口: from={window['from'] or '当前'} · to={window['to'] or window['from'] or '当前'}")

    lines.append(f"建议: {payload['recommendation']['command']} — {payload['recommendation']['reason']}")
    lines.append(f"路线图主下一步: {payload['nextTask']}")

    if payload["resumeFiles"]:
        lines.append("恢复入口:")
        lines.extend(f"- {item}" for item in payload["resumeFiles"])

    lines.append("执行步骤:")
    lines.extend(f"- {item}" for item in payload["steps"])

    if payload["blockers"]:
        lines.append("阻塞项:")
        lines.extend(f"- {item}" for item in payload["blockers"])

    if payload["validationDebt"]:
        lines.append("验证欠债:")
        lines.extend(f"- {item}" for item in payload["validationDebt"])

    if payload["warnings"]:
        lines.append("Warnings:")
        lines.extend(f"- {item}" for item in payload["warnings"])

    return "\n".join(lines)


def run_cli(default_mode: str) -> int:
    args = parse_args(__import__("sys").argv[1:])
    mode = args.mode or default_mode
    start_dir = Path(args.cwd)

    if mode == "progress":
        payload = collect_progress_snapshot(start_dir)
        output = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else format_progress(payload)
    elif mode == "report":
        payload = collect_session_report(start_dir)
        output = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else format_session_report(payload)
    elif mode == "pause":
        payload = pause_project(start_dir, note=args.note, stop_point=args.stop_point)
        output = (
            json.dumps(payload, ensure_ascii=False, indent=2)
            if args.json
            else f"Paused to {payload['handoffFile']}\n下一步: {payload['nextSteps'][0] if payload['nextSteps'] else '未记录'}"
        )
    elif mode == "resume":
        payload = resume_project(start_dir)
        output = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else format_resume(payload)
    elif mode == "next":
        payload = collect_progress_snapshot(start_dir)
        recommendation = payload["recommendation"]
        output = json.dumps(recommendation, ensure_ascii=False, indent=2) if args.json else f"{recommendation['command']} — {recommendation['reason']}"
    elif mode == "autonomous":
        payload = collect_autonomous_plan(
            start_dir,
            from_index=args.from_index,
            to_index=args.to_index,
            only=args.only,
            interactive=args.interactive,
        )
        output = json.dumps(payload, ensure_ascii=False, indent=2) if args.json else format_autonomous_plan(payload)
    else:
        raise SystemExit(f"Unsupported mode: {mode}")

    print(output)
    return 0
