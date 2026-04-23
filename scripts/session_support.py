from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from opc_common import find_opc_dir

try:
    from engine.decision_engine import DecisionEngine
    from engine.event_bus import get_event_bus
    from engine.state_engine import get_state_engine

    _V2_AVAILABLE = True
except ImportError:
    _V2_AVAILABLE = False


def read_recent_audit_lines(audit_log: Path, limit: int = 10) -> list[str]:
    try:
        lines = audit_log.read_text(encoding="utf-8").splitlines()
        return lines[-limit:]
    except OSError:
        return []


def get_v2_bus(project_root: Path | None = None) -> Any:
    if not _V2_AVAILABLE:
        return None
    try:
        opc_dir = find_opc_dir(project_root or Path.cwd())
        journal_dir = opc_dir / "events" if opc_dir else None
        if journal_dir:
            journal_dir.mkdir(parents=True, exist_ok=True)
        return get_event_bus(journal_dir=journal_dir)
    except Exception:
        return None


def normalize_user_command(command: str) -> str:
    normalized = " ".join(str(command).strip().split())
    if not normalized:
        return normalized

    legacy_map = {
        "/opc-discuss": "/opc discuss",
        "/opc-explore": "/opc explore",
        "/opc-fast": "/opc fast",
        "/opc-next": "/opc next",
        "/opc-quick": "/opc quick",
    }
    if normalized in legacy_map:
        return legacy_map[normalized]

    runtime_map = {
        "opc-tools intel status": "/opc-intel status",
        "opc-tools verify health": "/opc-health",
        "python scripts/opc_dashboard.py": "/opc-dashboard",
        "python scripts/opc_health.py": "/opc-health",
    }
    for prefix, replacement in runtime_map.items():
        if normalized.startswith(prefix):
            return replacement

    return normalized


def _v2_decision_recommendation(insights: dict[str, Any]) -> dict[str, str] | None:
    if not _V2_AVAILABLE:
        return None
    try:
        project_root = Path(insights.get("projectRoot", "."))
        opc_dir = find_opc_dir(project_root)
        if not opc_dir:
            return None

        bus = get_event_bus()
        se = get_state_engine(opc_dir, bus)
        se.load()

        debt = insights.get("debt", {})
        blocker_items = debt.get("blockerItems", [])
        if blocker_items and not se.state.blockers:
            for blocker in blocker_items:
                se.state.blockers.append(blocker)

        context: dict[str, Any] = {}
        if (opc_dir / "HANDOFF.json").exists():
            context["handoff_exists"] = True
        if insights.get("validationDebt"):
            context["quality_violations"] = insights["validationDebt"]

        decision = DecisionEngine(se, bus).decide(context)
        return {
            "command": normalize_user_command(decision.command),
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
            "command": "/opc discuss",
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
            "command": "/opc next",
            "reason": f"路线图中的下一个未完成项是：{next_task}",
        }
    return {
        "command": "/opc discuss",
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
