#!/usr/bin/env python3
"""
profile_engine.py — Developer profiling for SuperOPC v2.

Automatically infers and maintains an 8-dimension developer profile
across sessions and projects.  The profile influences decision-engine
weighting, communication style, and explanation depth.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from event_bus import EventBus, get_event_bus


# ---------------------------------------------------------------------------
# Profile dimensions (inspired by GSD 8-dimension profiling)
# ---------------------------------------------------------------------------

@dataclass
class DeveloperProfile:
    communication_style: str = "balanced"
    decision_pattern: str = "analytical"
    debugging_preference: str = "systematic"
    ux_aesthetic: str = "minimalist"
    tech_stack_affinity: list[str] = field(default_factory=list)
    friction_triggers: list[str] = field(default_factory=list)
    learning_style: str = "hands-on"
    explanation_depth: str = "moderate"

    interaction_count: int = 0
    projects_seen: list[str] = field(default_factory=list)
    preferred_commands: dict[str, int] = field(default_factory=dict)
    session_patterns: dict[str, Any] = field(default_factory=dict)

    updated_at: str = ""
    version: str = "1.0.0"


COMMUNICATION_STYLES = ("terse", "balanced", "verbose")
DECISION_PATTERNS = ("intuitive", "analytical", "consensus-seeking")
DEBUGGING_PREFS = ("systematic", "intuitive", "log-driven")
UX_AESTHETICS = ("minimalist", "feature-rich", "data-dense")
LEARNING_STYLES = ("hands-on", "conceptual", "example-driven")
EXPLANATION_DEPTHS = ("brief", "moderate", "deep")


# ---------------------------------------------------------------------------
# ProfileEngine
# ---------------------------------------------------------------------------

class ProfileEngine:
    """Maintains a global developer profile at ~/.opc/USER-PROFILE.json."""

    GLOBAL_DIR = Path.home() / ".opc"

    def __init__(self, *, profile_dir: Path | None = None, bus: EventBus | None = None):
        self._dir = profile_dir or self.GLOBAL_DIR
        self._file = self._dir / "USER-PROFILE.json"
        self._bus = bus or get_event_bus()
        self._profile: DeveloperProfile | None = None

    def load(self) -> DeveloperProfile:
        if self._file.exists():
            try:
                data = json.loads(self._file.read_text(encoding="utf-8"))
                self._profile = self._dict_to_profile(data)
            except (json.JSONDecodeError, OSError):
                self._profile = DeveloperProfile()
        else:
            self._profile = DeveloperProfile()
        return self._profile

    @property
    def profile(self) -> DeveloperProfile:
        if self._profile is None:
            return self.load()
        return self._profile

    def save(self) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        self._profile.updated_at = _now()
        self._file.write_text(
            json.dumps(asdict(self.profile), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def record_interaction(self, *, command: str = "", project: str = "", signals: dict[str, Any] | None = None) -> None:
        p = self.profile
        p.interaction_count += 1

        if command:
            p.preferred_commands[command] = p.preferred_commands.get(command, 0) + 1

        if project and project not in p.projects_seen:
            p.projects_seen.append(project)

        if signals:
            self._apply_signals(signals)

        self.save()
        self._bus.publish("profile.updated", {"interaction_count": p.interaction_count}, source="profile_engine")

    def _apply_signals(self, signals: dict[str, Any]) -> None:
        p = self.profile

        if "tech_stack" in signals:
            stack = signals["tech_stack"]
            if isinstance(stack, str) and stack not in p.tech_stack_affinity:
                p.tech_stack_affinity.append(stack)
            elif isinstance(stack, list):
                for s in stack:
                    if s not in p.tech_stack_affinity:
                        p.tech_stack_affinity.append(s)

        if "friction" in signals:
            fric = signals["friction"]
            if isinstance(fric, str) and fric not in p.friction_triggers:
                p.friction_triggers.append(fric)

        for dim, valid in [
            ("communication_style", COMMUNICATION_STYLES),
            ("decision_pattern", DECISION_PATTERNS),
            ("debugging_preference", DEBUGGING_PREFS),
            ("ux_aesthetic", UX_AESTHETICS),
            ("learning_style", LEARNING_STYLES),
            ("explanation_depth", EXPLANATION_DEPTHS),
        ]:
            if dim in signals and signals[dim] in valid:
                setattr(p, dim, signals[dim])

    def infer_from_session(self, session_data: dict[str, Any]) -> None:
        signals: dict[str, Any] = {}

        commands_used = session_data.get("commands", [])
        if commands_used:
            quick_count = sum(1 for c in commands_used if c in ("/opc-fast", "/opc-quick"))
            plan_count = sum(1 for c in commands_used if c in ("/opc-plan", "/opc-discuss"))
            if quick_count > plan_count * 2:
                signals["communication_style"] = "terse"
                signals["decision_pattern"] = "intuitive"
            elif plan_count > quick_count * 2:
                signals["communication_style"] = "verbose"
                signals["decision_pattern"] = "analytical"

        tech_detected = session_data.get("tech_stack", [])
        if tech_detected:
            signals["tech_stack"] = tech_detected

        if signals:
            self._apply_signals(signals)
            self.save()

    def get_context_injection(self) -> dict[str, Any]:
        p = self.profile
        return {
            "developer_profile": {
                "style": p.communication_style,
                "depth": p.explanation_depth,
                "decision": p.decision_pattern,
                "stack": p.tech_stack_affinity[:5],
                "interactions": p.interaction_count,
            }
        }

    def generate_questionnaire(self) -> list[dict[str, Any]]:
        """Generate 6-question quick profiling questionnaire."""
        return [
            {
                "id": "q1_communication",
                "question": "你希望我的回复风格是？",
                "options": [
                    {"key": "A", "label": "简洁直接，少废话", "maps_to": {"communication_style": "terse"}},
                    {"key": "B", "label": "适度详细", "maps_to": {"communication_style": "balanced"}},
                    {"key": "C", "label": "充分解释每个决策", "maps_to": {"communication_style": "verbose"}},
                ],
            },
            {
                "id": "q2_decision",
                "question": "做技术决策时，你更倾向？",
                "options": [
                    {"key": "A", "label": "跟着感觉快速决定", "maps_to": {"decision_pattern": "intuitive"}},
                    {"key": "B", "label": "看数据和对比再决定", "maps_to": {"decision_pattern": "analytical"}},
                    {"key": "C", "label": "讨论后一起决定", "maps_to": {"decision_pattern": "consensus-seeking"}},
                ],
            },
            {
                "id": "q3_debugging",
                "question": "遇到 bug 时，你通常？",
                "options": [
                    {"key": "A", "label": "系统化缩小范围", "maps_to": {"debugging_preference": "systematic"}},
                    {"key": "B", "label": "凭直觉跳到可能的原因", "maps_to": {"debugging_preference": "intuitive"}},
                    {"key": "C", "label": "先加日志看发生了什么", "maps_to": {"debugging_preference": "log-driven"}},
                ],
            },
            {
                "id": "q4_ux",
                "question": "UI/UX 方面你偏好？",
                "options": [
                    {"key": "A", "label": "极简，功能为王", "maps_to": {"ux_aesthetic": "minimalist"}},
                    {"key": "B", "label": "功能丰富，什么都能做", "maps_to": {"ux_aesthetic": "feature-rich"}},
                    {"key": "C", "label": "数据密集，一屏看全", "maps_to": {"ux_aesthetic": "data-dense"}},
                ],
            },
            {
                "id": "q5_learning",
                "question": "学新东西时你更喜欢？",
                "options": [
                    {"key": "A", "label": "直接动手做", "maps_to": {"learning_style": "hands-on"}},
                    {"key": "B", "label": "先理解原理", "maps_to": {"learning_style": "conceptual"}},
                    {"key": "C", "label": "看示例代码", "maps_to": {"learning_style": "example-driven"}},
                ],
            },
            {
                "id": "q6_depth",
                "question": "解释事情时你希望多详细？",
                "options": [
                    {"key": "A", "label": "最短能理解就行", "maps_to": {"explanation_depth": "brief"}},
                    {"key": "B", "label": "适当展开", "maps_to": {"explanation_depth": "moderate"}},
                    {"key": "C", "label": "完整深入", "maps_to": {"explanation_depth": "deep"}},
                ],
            },
        ]

    def apply_questionnaire_answers(self, answers: dict[str, str]) -> None:
        """Apply questionnaire answers to profile. answers = {question_id: option_key}."""
        questions = {q["id"]: q for q in self.generate_questionnaire()}
        signals: dict[str, Any] = {}
        for q_id, answer_key in answers.items():
            if q_id not in questions:
                continue
            for opt in questions[q_id]["options"]:
                if opt["key"] == answer_key.upper():
                    signals.update(opt["maps_to"])
                    break
        if signals:
            self._apply_signals(signals)
            self.save()
            self._bus.publish("profile.questionnaire_completed", signals, source="profile_engine")

    def export_markdown(self) -> str:
        """Export profile as human-readable USER-PROFILE.md content."""
        p = self.profile
        stack_str = ", ".join(p.tech_stack_affinity[:10]) if p.tech_stack_affinity else "未检测"
        friction_str = ", ".join(p.friction_triggers[:10]) if p.friction_triggers else "无记录"
        top_cmds = sorted(p.preferred_commands.items(), key=lambda x: -x[1])[:5]
        cmds_str = ", ".join(f"`{c}` ({n}次)" for c, n in top_cmds) if top_cmds else "无记录"

        return f"""# 开发者画像 — SuperOPC

> 生成时间: {_now()} | 交互次数: {p.interaction_count} | 版本: {p.version}

## 8 维度

| 维度 | 当前值 | 含义 |
|------|--------|------|
| 沟通风格 | **{p.communication_style}** | {_STYLE_DESC.get(p.communication_style, "")} |
| 决策模式 | **{p.decision_pattern}** | {_DECISION_DESC.get(p.decision_pattern, "")} |
| 调试方式 | **{p.debugging_preference}** | {_DEBUG_DESC.get(p.debugging_preference, "")} |
| UX 偏好 | **{p.ux_aesthetic}** | {_UX_DESC.get(p.ux_aesthetic, "")} |
| 技术栈 | {stack_str} | 自动检测 |
| 摩擦触发 | {friction_str} | 自动检测 |
| 学习风格 | **{p.learning_style}** | {_LEARN_DESC.get(p.learning_style, "")} |
| 解释深度 | **{p.explanation_depth}** | {_DEPTH_DESC.get(p.explanation_depth, "")} |

## 行为统计

- **常用命令**: {cmds_str}
- **接触项目**: {len(p.projects_seen)} 个
- **总交互**: {p.interaction_count} 次

## 系统适配

基于此画像，SuperOPC 将：
{"- 回复简洁直接，省略过程解释" if p.communication_style == "terse" else ""}{"- 回复充分展示决策原因和替代方案" if p.communication_style == "verbose" else ""}{"- 减少确认步骤，快速执行" if p.decision_pattern == "intuitive" else ""}{"- 每步展示数据支撑和权衡分析" if p.decision_pattern == "analytical" else ""}{"- 调试时遵循假设→证据→排除流程" if p.debugging_preference == "systematic" else ""}{"- 调试时优先添加日志语句" if p.debugging_preference == "log-driven" else ""}{"- 提供简短一行总结" if p.explanation_depth == "brief" else ""}{"- 包含背景知识和扩展阅读" if p.explanation_depth == "deep" else ""}

---
*使用 `/opc-profile --refresh` 重新校准画像*
"""

    def save_markdown(self, target_dir: Path | None = None) -> Path:
        """Save profile as USER-PROFILE.md to the specified directory."""
        out_dir = target_dir or self._dir
        out_dir.mkdir(parents=True, exist_ok=True)
        out_file = out_dir / "USER-PROFILE.md"
        out_file.write_text(self.export_markdown(), encoding="utf-8")
        return out_file

    @staticmethod
    def _dict_to_profile(data: dict[str, Any]) -> DeveloperProfile:
        known_fields = {f.name for f in DeveloperProfile.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return DeveloperProfile(**filtered)


# ---------------------------------------------------------------------------
# Dimension descriptions (Chinese)
# ---------------------------------------------------------------------------

_STYLE_DESC = {
    "terse": "简洁直接，少废话",
    "balanced": "适度详细",
    "verbose": "充分解释每个决策",
}
_DECISION_DESC = {
    "intuitive": "跟着感觉快速决定",
    "analytical": "看数据和对比再决定",
    "consensus-seeking": "讨论后一起决定",
}
_DEBUG_DESC = {
    "systematic": "系统化缩小范围",
    "intuitive": "凭直觉跳到可能的原因",
    "log-driven": "先加日志看发生了什么",
}
_UX_DESC = {
    "minimalist": "极简，功能为王",
    "feature-rich": "功能丰富，什么都能做",
    "data-dense": "数据密集，一屏看全",
}
_LEARN_DESC = {
    "hands-on": "直接动手做",
    "conceptual": "先理解原理",
    "example-driven": "看示例代码",
}
_DEPTH_DESC = {
    "brief": "最短能理解就行",
    "moderate": "适当展开",
    "deep": "完整深入",
}


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
