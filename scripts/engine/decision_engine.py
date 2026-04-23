#!/usr/bin/env python3
"""
decision_engine.py — The brain of SuperOPC v2.

Three-layer decision architecture:
  Layer 1: Rule engine   — deterministic responses to known patterns
  Layer 2: State machine — flow-aware decisions based on project phase
  Layer 3: Heuristic     — ICE-scored priority ranking for ambiguous situations

Integrates with the event bus (reacts to events) and emits
`decision.made` / `decision.required` events for downstream consumers.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from engine.event_bus import Event, EventBus, get_event_bus
from engine.state_engine import ProjectPhase, ProjectState, StateEngine


# ---------------------------------------------------------------------------
# Decision model
# ---------------------------------------------------------------------------

class ActionZone(str, Enum):
    GREEN = "green"
    YELLOW = "yellow"
    RED = "red"


class ActionType(str, Enum):
    HEALTH_CHECK = "health_check"
    RUN_TESTS = "run_tests"
    GENERATE_DOCS = "generate_docs"
    COLLECT_INTEL = "collect_intel"
    FORMAT_CODE = "format_code"
    CODE_CHANGE = "code_change"
    DEPENDENCY_UPGRADE = "dependency_upgrade"
    PHASE_ADVANCE = "phase_advance"
    CREATE_PR = "create_pr"
    DEPLOY = "deploy"
    DB_MIGRATION = "db_migration"
    SECURITY_CONFIG = "security_config"
    PAYMENT_ACTION = "payment_action"
    DISCUSS = "discuss"
    PLAN = "plan"
    BUILD = "build"
    REVIEW = "review"
    SHIP = "ship"
    DEBUG = "debug"
    RESEARCH = "research"
    RESUME = "resume"
    PAUSE = "pause"
    WAIT = "wait"


ZONE_MAP: dict[ActionType, ActionZone] = {
    ActionType.HEALTH_CHECK: ActionZone.GREEN,
    ActionType.RUN_TESTS: ActionZone.GREEN,
    ActionType.GENERATE_DOCS: ActionZone.GREEN,
    ActionType.COLLECT_INTEL: ActionZone.GREEN,
    ActionType.FORMAT_CODE: ActionZone.GREEN,
    ActionType.RESEARCH: ActionZone.GREEN,
    ActionType.CODE_CHANGE: ActionZone.YELLOW,
    ActionType.DEPENDENCY_UPGRADE: ActionZone.YELLOW,
    ActionType.PHASE_ADVANCE: ActionZone.YELLOW,
    ActionType.CREATE_PR: ActionZone.YELLOW,
    ActionType.BUILD: ActionZone.YELLOW,
    ActionType.REVIEW: ActionZone.YELLOW,
    ActionType.DISCUSS: ActionZone.YELLOW,
    ActionType.PLAN: ActionZone.YELLOW,
    ActionType.DEBUG: ActionZone.YELLOW,
    ActionType.RESUME: ActionZone.YELLOW,
    ActionType.PAUSE: ActionZone.GREEN,
    ActionType.WAIT: ActionZone.GREEN,
    ActionType.DEPLOY: ActionZone.RED,
    ActionType.DB_MIGRATION: ActionZone.RED,
    ActionType.SECURITY_CONFIG: ActionZone.RED,
    ActionType.PAYMENT_ACTION: ActionZone.RED,
    ActionType.SHIP: ActionZone.RED,
}


@dataclass
class Decision:
    action: ActionType
    zone: ActionZone
    command: str
    reason: str
    confidence: float = 0.0
    context: dict[str, Any] = field(default_factory=dict)
    requires_approval: bool = False
    timestamp: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["action"] = self.action.value
        d["zone"] = self.zone.value
        return d


# ---------------------------------------------------------------------------
# Layer 1: Rule Engine
# ---------------------------------------------------------------------------

class RuleEngine:
    """Deterministic pattern-matching rules that produce immediate decisions."""

    def evaluate(self, state: ProjectState, context: dict[str, Any]) -> Decision | None:
        if state.blockers:
            return Decision(
                action=ActionType.DISCUSS,
                zone=ActionZone.YELLOW,
                command="/opc discuss",
                reason=f"{len(state.blockers)} blocker(s) detected — must resolve before execution.",
                confidence=0.95,
                requires_approval=False,
            )

        if context.get("handoff_exists"):
            return Decision(
                action=ActionType.RESUME,
                zone=ActionZone.YELLOW,
                command="/opc-resume",
                reason="HANDOFF.json found — recovering previous session context.",
                confidence=0.90,
                requires_approval=False,
            )

        if context.get("quality_violations"):
            violations = context["quality_violations"]
            if any("secret" in str(v).lower() or "injection" in str(v).lower() for v in violations):
                return Decision(
                    action=ActionType.SECURITY_CONFIG,
                    zone=ActionZone.RED,
                    command="/opc-review",
                    reason="Security violation detected — requires human review.",
                    confidence=0.98,
                    requires_approval=True,
                )
            return Decision(
                action=ActionType.HEALTH_CHECK,
                zone=ActionZone.GREEN,
                command="/opc-health",
                reason=f"{len(violations)} quality issue(s) found — inspect health before proceeding.",
                confidence=0.85,
            )

        if context.get("test_failures"):
            return Decision(
                action=ActionType.DEBUG,
                zone=ActionZone.YELLOW,
                command="/opc-debug",
                reason="Test failures detected — triggering debugger pipeline.",
                confidence=0.88,
            )

        if state.validation_debt:
            return Decision(
                action=ActionType.RUN_TESTS,
                zone=ActionZone.GREEN,
                command="opc-tools verify health",
                reason=f"{len(state.validation_debt)} validation debt item(s) — verify before proceeding.",
                confidence=0.86,
            )

        return None


# ---------------------------------------------------------------------------
# Layer 2: State Machine
# ---------------------------------------------------------------------------

class StateMachineEngine:
    """Phase-aware decisions based on current project status."""

    PHASE_ACTIONS: dict[ProjectPhase, tuple[ActionType, str, str]] = {
        ProjectPhase.IDLE: (ActionType.PLAN, "/opc-plan", "Project idle — initiate planning for next milestone."),
        ProjectPhase.DISCUSSING: (ActionType.PLAN, "/opc-plan", "Discussion phase — converge on plan."),
        ProjectPhase.PLANNING: (ActionType.BUILD, "/opc-build", "Plan ready — begin execution."),
        ProjectPhase.EXECUTING: (ActionType.BUILD, "/opc-build", "Execution in progress — continue building."),
        ProjectPhase.REVIEWING: (ActionType.REVIEW, "/opc-review", "Review phase — complete code review."),
        ProjectPhase.SHIPPING: (ActionType.SHIP, "/opc-ship", "Shipping phase — verify and release."),
        ProjectPhase.PAUSED: (ActionType.RESUME, "/opc-resume", "Project paused — resume from last checkpoint."),
    }

    def evaluate(self, state: ProjectState) -> Decision:
        action_type, command, reason = self.PHASE_ACTIONS.get(
            state.status,
            (ActionType.DISCUSS, "/opc discuss", "Unknown state — discuss to clarify direction."),
        )
        zone = ZONE_MAP.get(action_type, ActionZone.YELLOW)
        return Decision(
            action=action_type,
            zone=zone,
            command=command,
            reason=reason,
            confidence=0.70,
            requires_approval=zone == ActionZone.RED,
        )


# ---------------------------------------------------------------------------
# Layer 3: Heuristic Scoring (ICE)
# ---------------------------------------------------------------------------

@dataclass
class ScoredOption:
    action: ActionType
    command: str
    reason: str
    impact: float = 0.0
    confidence: float = 0.0
    ease: float = 0.0

    @property
    def ice_score(self) -> float:
        return self.impact * self.confidence * self.ease


class HeuristicEngine:
    """ICE-scored priority ranking for ambiguous multi-option decisions."""

    def rank(self, state: ProjectState, context: dict[str, Any]) -> list[ScoredOption]:
        options: list[ScoredOption] = []

        if state.status in (ProjectPhase.IDLE, ProjectPhase.PAUSED):
            next_task = context.get("next_roadmap_task", "")
            if next_task:
                options.append(ScoredOption(
                    action=ActionType.PLAN,
                    command="/opc-plan",
                    reason=f"Roadmap next: {next_task}",
                    impact=0.8, confidence=0.7, ease=0.8,
                ))

            options.append(ScoredOption(
                action=ActionType.COLLECT_INTEL,
                command="/opc-intel status",
                reason="Inspect current codebase intelligence before planning.",
                impact=0.6, confidence=0.8, ease=0.9,
            ))

        if context.get("tech_debt_count", 0) > 5:
            options.append(ScoredOption(
                action=ActionType.CODE_CHANGE,
                command="/opc-build",
                reason=f"High tech debt ({context['tech_debt_count']} items) — refactoring recommended.",
                impact=0.7, confidence=0.8, ease=0.5,
            ))

        if context.get("days_since_release", 999) > 14:
            options.append(ScoredOption(
                action=ActionType.SHIP,
                command="/opc-ship",
                reason="No release in 14+ days — consider shipping current progress.",
                impact=0.9, confidence=0.6, ease=0.4,
            ))

        options.append(ScoredOption(
            action=ActionType.HEALTH_CHECK,
            command="/opc-health",
            reason="Periodic health check.",
            impact=0.4, confidence=0.9, ease=0.95,
        ))

        return sorted(options, key=lambda o: o.ice_score, reverse=True)


# ---------------------------------------------------------------------------
# DecisionEngine (orchestrates all three layers)
# ---------------------------------------------------------------------------

class DecisionEngine:
    """Unified decision-making: rules → state machine → heuristics."""

    def __init__(self, state_engine: StateEngine, bus: EventBus | None = None):
        self._state_engine = state_engine
        self._bus = bus or get_event_bus()
        self._rules = RuleEngine()
        self._sm = StateMachineEngine()
        self._heuristic = HeuristicEngine()
        self._history: list[Decision] = []

    def decide(self, context: dict[str, Any] | None = None) -> Decision:
        ctx = context or {}
        state = self._state_engine.state

        rule_decision = self._rules.evaluate(state, ctx)
        if rule_decision and rule_decision.confidence >= 0.85:
            rule_decision.context = {"layer": "rules", "state": state.status.value}
            self._record(rule_decision)
            return rule_decision

        sm_decision = self._sm.evaluate(state)

        ranked = self._heuristic.rank(state, ctx)
        if ranked and ranked[0].ice_score > sm_decision.confidence:
            top = ranked[0]
            decision = Decision(
                action=top.action,
                zone=ZONE_MAP.get(top.action, ActionZone.YELLOW),
                command=top.command,
                reason=top.reason,
                confidence=top.ice_score,
                requires_approval=ZONE_MAP.get(top.action, ActionZone.YELLOW) == ActionZone.RED,
                context={"layer": "heuristic", "ice_score": top.ice_score, "state": state.status.value},
            )
            self._record(decision)
            return decision

        sm_decision.context = {"layer": "state_machine", "state": state.status.value}
        self._record(sm_decision)
        return sm_decision

    def _record(self, decision: Decision) -> None:
        self._history.append(decision)
        if len(self._history) > 200:
            self._history = self._history[-200:]

        self._bus.publish(
            "decision.made",
            decision.to_dict(),
            source="decision_engine",
        )

    @property
    def history(self) -> list[Decision]:
        return list(self._history)

    def recent_decisions(self, n: int = 10) -> list[dict[str, Any]]:
        return [d.to_dict() for d in self._history[-n:]]

    def persist_history(self, filepath: Path) -> None:
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = [d.to_dict() for d in self._history]
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
