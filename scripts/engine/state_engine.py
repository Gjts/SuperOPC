#!/usr/bin/env python3
"""
state_engine.py — Structured state management for SuperOPC v2.

Upgrades the flat `.opc/STATE.md` into a dual-write system (JSON truth +
Markdown presentation).  Emits events on every state transition so
downstream systems (decision engine, cruise controller, etc.) can react.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from event_bus import Event, EventBus, get_event_bus


# ---------------------------------------------------------------------------
# State model
# ---------------------------------------------------------------------------

class ProjectPhase(str, Enum):
    IDLE = "idle"
    DISCUSSING = "discussing"
    PLANNING = "planning"
    EXECUTING = "executing"
    REVIEWING = "reviewing"
    SHIPPING = "shipping"
    PAUSED = "paused"


VALID_TRANSITIONS: dict[ProjectPhase, frozenset[ProjectPhase]] = {
    ProjectPhase.IDLE: frozenset({ProjectPhase.DISCUSSING, ProjectPhase.PLANNING, ProjectPhase.EXECUTING, ProjectPhase.PAUSED}),
    ProjectPhase.DISCUSSING: frozenset({ProjectPhase.PLANNING, ProjectPhase.IDLE, ProjectPhase.PAUSED}),
    ProjectPhase.PLANNING: frozenset({ProjectPhase.EXECUTING, ProjectPhase.DISCUSSING, ProjectPhase.IDLE, ProjectPhase.PAUSED}),
    ProjectPhase.EXECUTING: frozenset({ProjectPhase.REVIEWING, ProjectPhase.PLANNING, ProjectPhase.IDLE, ProjectPhase.PAUSED}),
    ProjectPhase.REVIEWING: frozenset({ProjectPhase.SHIPPING, ProjectPhase.EXECUTING, ProjectPhase.PLANNING, ProjectPhase.IDLE, ProjectPhase.PAUSED}),
    ProjectPhase.SHIPPING: frozenset({ProjectPhase.IDLE, ProjectPhase.PAUSED}),
    ProjectPhase.PAUSED: frozenset({ProjectPhase.IDLE, ProjectPhase.DISCUSSING, ProjectPhase.PLANNING, ProjectPhase.EXECUTING, ProjectPhase.REVIEWING}),
}


@dataclass
class ProjectState:
    project_name: str = "Unnamed Project"
    current_focus: str = ""
    status: ProjectPhase = ProjectPhase.IDLE
    phase_current: int = 0
    phase_total: int = 0
    phase_name: str = ""
    plan_current: int = 0
    plan_total: int = 0
    recent_activity: str = ""
    last_session: str = ""
    stop_point: str = ""
    resume_file: str = ""
    blockers: list[str] = field(default_factory=list)
    todos: list[str] = field(default_factory=list)
    validation_debt: list[str] = field(default_factory=list)
    business_metrics: dict[str, str] = field(default_factory=dict)
    updated_at: str = ""


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# StateEngine
# ---------------------------------------------------------------------------

class StateEngine:
    """Manages project state with dual-write (JSON + Markdown) and event emission."""

    def __init__(self, opc_dir: Path, bus: EventBus | None = None):
        self._opc_dir = opc_dir
        self._bus = bus or get_event_bus(opc_dir / "events")
        self._state_json = opc_dir / "state.json"
        self._state_md = opc_dir / "STATE.md"
        self._state: ProjectState | None = None

    @property
    def opc_dir(self) -> Path:
        return self._opc_dir

    def load(self) -> ProjectState:
        if self._state_json.exists():
            self._state = self._load_from_json()
        elif self._state_md.exists():
            self._state = self._parse_legacy_md()
        else:
            self._state = ProjectState()
        return self._state

    @property
    def state(self) -> ProjectState:
        if self._state is None:
            return self.load()
        return self._state

    def transition(self, new_status: ProjectPhase, *, reason: str = "") -> bool:
        current = self.state.status
        if new_status not in VALID_TRANSITIONS.get(current, frozenset()):
            return False

        old_status = current
        self._state.status = new_status
        self._state.recent_activity = f"{_now_iso()} — {old_status.value} -> {new_status.value}: {reason}"
        self._state.updated_at = _now_iso()
        self.save()

        self._bus.publish(
            "phase.start" if new_status != ProjectPhase.PAUSED else "session.end",
            {"from": old_status.value, "to": new_status.value, "reason": reason},
            source="state_engine",
        )
        return True

    def update(self, **kwargs: Any) -> None:
        state = self.state
        changed_fields: list[str] = []
        for key, value in kwargs.items():
            if hasattr(state, key) and getattr(state, key) != value:
                setattr(state, key, value)
                changed_fields.append(key)

        if changed_fields:
            state.updated_at = _now_iso()
            self.save()

    def add_blocker(self, description: str) -> None:
        state = self.state
        if description not in state.blockers:
            state.blockers.append(description)
            state.updated_at = _now_iso()
            self.save()
            self._bus.publish("autonomous.blocked", {"blocker": description}, source="state_engine")

    def resolve_blocker(self, description: str) -> None:
        state = self.state
        if description in state.blockers:
            state.blockers.remove(description)
            state.updated_at = _now_iso()
            self.save()

    def save(self) -> None:
        self._opc_dir.mkdir(parents=True, exist_ok=True)
        self._write_json()
        self._write_markdown()

    # -- JSON persistence --

    def _write_json(self) -> None:
        data = asdict(self.state)
        data["status"] = self.state.status.value
        self._state_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_from_json(self) -> ProjectState:
        try:
            data = json.loads(self._state_json.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return ProjectState()

        status_raw = data.pop("status", "idle")
        try:
            status = ProjectPhase(status_raw)
        except ValueError:
            status = ProjectPhase.IDLE

        return ProjectState(status=status, **{k: v for k, v in data.items() if k != "status" and hasattr(ProjectState, k)})

    # -- Markdown persistence (human-readable mirror) --

    def _write_markdown(self) -> None:
        s = self.state
        phase_str = f"[{s.phase_current}] / [{s.phase_total}]（{s.phase_name}）" if s.phase_total else "未记录"
        plan_str = f"[{s.plan_current}] / [{s.plan_total}]" if s.plan_total else "未记录"
        blockers_md = "\n".join(f"- {b}" for b in s.blockers) if s.blockers else "- 暂无"
        todos_md = "\n".join(f"- {t}" for t in s.todos) if s.todos else "- 暂无"
        vdebt_md = "\n".join(f"- {v}" for v in s.validation_debt) if s.validation_debt else "- 暂无"
        biz = s.business_metrics
        mrr = biz.get("mrr", "未记录")
        burn = biz.get("burn", "未记录")
        runway = biz.get("runway", "未记录")
        customers = biz.get("customers", "未记录")

        md = f"""# {s.project_name}

## 活状态

**当前焦点：** {s.current_focus or '未记录'}
**核心价值：** 未记录
**状态：** {s.status.value}
**阶段：** {phase_str}
**计划：** {plan_str}
**最近活动：** {s.recent_activity or '未记录'}
**上次会话：** {s.last_session or '未记录'}
**停止于：** {s.stop_point or '未记录'}
**恢复文件：** {s.resume_file or '未记录'}

## 阻塞/关注

{blockers_md}

## 待办事项

{todos_md}

## 验证欠债

{vdebt_md}

## 商业指标

- MRR：{mrr}
- Burn：{burn}
- Runway：{runway}
- Active Customers：{customers}

---
_Last updated: {s.updated_at or _now_iso()}_
"""
        self._state_md.write_text(md, encoding="utf-8")

    # -- Legacy markdown parser --

    def _parse_legacy_md(self) -> ProjectState:
        try:
            text = self._state_md.read_text(encoding="utf-8")
        except OSError:
            return ProjectState()

        def _extract(label: str) -> str:
            for sep in ("：", ":"):
                pattern = rf"(?:\*\*)?{re.escape(label)}(?:\*\*)?\s*{re.escape(sep)}\s*(.+)$"
                m = re.search(pattern, text, re.MULTILINE)
                if m:
                    return m.group(1).strip()
            return ""

        name_match = re.search(r"^#\s+(.+)$", text, re.MULTILINE)
        phase_match = re.search(r"阶段[：:]\s*\[(.+?)\]\s*/\s*\[(.+?)\]\s*（(.+?)）", text)
        plan_match = re.search(r"计划[：:]\s*\[(.+?)\]\s*/\s*\[(.+?)\]", text)

        status_raw = _extract("状态")
        status_map = {
            "idle": ProjectPhase.IDLE,
            "discussing": ProjectPhase.DISCUSSING,
            "准备规划": ProjectPhase.PLANNING,
            "规划中": ProjectPhase.PLANNING,
            "准备执行": ProjectPhase.EXECUTING,
            "执行中": ProjectPhase.EXECUTING,
            "阶段完成": ProjectPhase.REVIEWING,
            "paused": ProjectPhase.PAUSED,
        }
        status = status_map.get(status_raw.lower(), ProjectPhase.IDLE)

        return ProjectState(
            project_name=name_match.group(1).strip() if name_match else "Unnamed",
            current_focus=_extract("当前焦点"),
            status=status,
            phase_current=int(phase_match.group(1)) if phase_match else 0,
            phase_total=int(phase_match.group(2)) if phase_match else 0,
            phase_name=phase_match.group(3) if phase_match else "",
            plan_current=int(plan_match.group(1)) if plan_match else 0,
            plan_total=int(plan_match.group(2)) if plan_match else 0,
            recent_activity=_extract("最近活动"),
            last_session=_extract("上次会话"),
            stop_point=_extract("停止于"),
            resume_file=_extract("恢复文件"),
            updated_at=_now_iso(),
        )


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def get_state_engine(opc_dir: Path, bus: EventBus | None = None) -> StateEngine:
    return StateEngine(opc_dir, bus=bus)
