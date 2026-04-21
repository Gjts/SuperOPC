#!/usr/bin/env python3
"""
context_assembler.py — Dynamic context construction for SuperOPC v2.

Replaces static CLAUDE.md injection with intelligent, phase-aware context
assembly.  Selects the most relevant skills, rules, references, agent
profiles, and historical learnings based on:
  - Current project phase
  - Developer profile
  - Available context window budget
  - Active task type
"""

from __future__ import annotations

import json
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from event_bus import EventBus, get_event_bus
from state_engine import ProjectPhase, ProjectState, StateEngine
from profile_engine import ProfileEngine
from learning_store import LearningStore

try:
    from intelligence.methodology_database import MethodologyDatabase
except ImportError:
    scripts_dir = str(Path(__file__).resolve().parent.parent)
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    from intelligence.methodology_database import MethodologyDatabase


# ---------------------------------------------------------------------------
# Budget tiers
# ---------------------------------------------------------------------------

@dataclass
class ContextBudget:
    """Token-approximate budget tiers for context window management."""
    total_tokens: int = 200_000
    skills_budget: float = 0.30
    rules_budget: float = 0.15
    references_budget: float = 0.10
    agents_budget: float = 0.10
    learnings_budget: float = 0.10
    state_budget: float = 0.15
    reserved: float = 0.10


BUDGET_PROFILES = {
    "compact": ContextBudget(total_tokens=128_000, skills_budget=0.25, learnings_budget=0.05),
    "standard": ContextBudget(total_tokens=200_000),
    "extended": ContextBudget(total_tokens=500_000, skills_budget=0.35, learnings_budget=0.15),
    "maximum": ContextBudget(total_tokens=1_000_000, skills_budget=0.35, learnings_budget=0.20, references_budget=0.15),
}


# ---------------------------------------------------------------------------
# Phase-to-skill relevance mapping
# ---------------------------------------------------------------------------

PHASE_SKILL_PRIORITY: dict[ProjectPhase, list[str]] = {
    ProjectPhase.IDLE: [
        "using-superopc", "workflow-modes", "business-advisory", "session-management",
    ],
    ProjectPhase.DISCUSSING: [
        "using-superopc", "workflow-modes", "planning", "business-advisory",
    ],
    ProjectPhase.PLANNING: [
        "planning", "business-advisory", "agent-dispatch", "verification-loop",
    ],
    ProjectPhase.EXECUTING: [
        "implementing", "tdd", "agent-dispatch",
        "git-worktrees", "debugging", "verification-loop",
    ],
    ProjectPhase.REVIEWING: [
        "reviewing", "security-review", "verification-loop", "shipping",
    ],
    ProjectPhase.SHIPPING: [
        "shipping", "security-review", "verification-loop", "git-worktrees",
    ],
    ProjectPhase.PAUSED: [
        "session-management", "using-superopc", "workflow-modes",
    ],
}

PHASE_AGENT_PRIORITY: dict[ProjectPhase, list[str]] = {
    ProjectPhase.IDLE: ["opc-orchestrator", "opc-researcher"],
    ProjectPhase.DISCUSSING: ["opc-researcher", "opc-planner", "opc-assumptions-analyzer"],
    ProjectPhase.PLANNING: ["opc-planner", "opc-plan-checker", "opc-assumptions-analyzer", "opc-roadmapper"],
    ProjectPhase.EXECUTING: ["opc-executor", "opc-debugger", "opc-frontend-wizard", "opc-backend-architect"],
    ProjectPhase.REVIEWING: ["opc-reviewer", "opc-security-auditor", "opc-ui-auditor", "opc-verifier"],
    ProjectPhase.SHIPPING: ["opc-verifier", "opc-doc-writer", "opc-doc-verifier"],
    ProjectPhase.PAUSED: ["opc-orchestrator"],
}

PHASE_RULES_PRIORITY: dict[ProjectPhase, list[str]] = {
    ProjectPhase.EXECUTING: ["testing", "coding-style", "security", "git-workflow"],
    ProjectPhase.REVIEWING: ["testing", "security", "patterns"],
    ProjectPhase.SHIPPING: ["git-workflow", "security"],
}

PHASE_REFERENCE_PRIORITY: dict[ProjectPhase, list[str]] = {
    ProjectPhase.IDLE: [
        "gates", "anti-patterns", "context-budget",
        "business/validate-idea", "business/find-community",
        "intelligence/market-research", "intelligence/follow-builders",
    ],
    ProjectPhase.DISCUSSING: [
        "gates", "anti-patterns", "business/validate-idea",
        "business/find-community", "business/user-interview",
        "intelligence/market-research",
    ],
    ProjectPhase.PLANNING: [
        "gates", "anti-patterns", "context-budget", "plan-template",
        "patterns/engineering/codebase-onboarding", "patterns/engineering/adr",
    ],
    ProjectPhase.EXECUTING: [
        "gates", "anti-patterns", "context-budget", "tdd",
        "verification-patterns", "git-integration",
        "patterns/engineering/api-design", "patterns/engineering/frontend",
        "patterns/engineering/backend",
    ],
    ProjectPhase.REVIEWING: [
        "gates", "anti-patterns", "review-rubric",
        "security-checklist", "verification-patterns",
        "patterns/engineering/e2e-testing",
    ],
    ProjectPhase.SHIPPING: [
        "gates", "anti-patterns", "git-integration",
        "security-checklist", "patterns/engineering/deployment",
        "patterns/engineering/docker", "business/seo", "business/content-engine",
    ],
    ProjectPhase.PAUSED: [
        "gates", "context-budget", "session-management", "handoff-format",
    ],
}


# ---------------------------------------------------------------------------
# ContextAssembler
# ---------------------------------------------------------------------------

class ContextAssembler:
    """Assembles the optimal context payload for the current state."""

    def __init__(
        self,
        repo_root: Path,
        state_engine: StateEngine,
        profile_engine: ProfileEngine | None = None,
        learning_store: LearningStore | None = None,
        methodology_db: MethodologyDatabase | None = None,
        bus: EventBus | None = None,
    ):
        self._root = repo_root
        self._state = state_engine
        self._profile = profile_engine or ProfileEngine()
        self._learnings = learning_store or LearningStore()
        self._methodologies = methodology_db or MethodologyDatabase(
            db_dir=repo_root / ".opc" / "intelligence" / "methodologies"
        )
        self._bus = bus or get_event_bus()

    def assemble(self, *, budget_profile: str = "standard", task_hint: str = "") -> dict[str, Any]:
        budget = BUDGET_PROFILES.get(budget_profile, BUDGET_PROFILES["standard"])
        state = self._state.state
        phase = state.status

        context: dict[str, Any] = {
            "budget": {
                "profile": budget_profile,
                "total_tokens": budget.total_tokens,
            },
            "project": {
                "name": state.project_name,
                "phase": phase.value,
                "focus": state.current_focus,
            },
            "skills": self._select_skills(phase, task_hint),
            "agents": self._select_agents(phase, task_hint),
            "rules": self._select_rules(phase),
            "references": self._select_references(phase),
            "learnings": self._select_learnings(state, task_hint),
            "methodologies": self._select_methodologies(phase, state, task_hint),
            "extracted_skills": self._select_extracted_skills(state, task_hint),
            "developer_profile": self._profile.get_context_injection(),
            "state_summary": self._state_summary(state),
            "behavior_protocol": self._behavior_protocol(phase),
        }

        return context

    def generate_dynamic_claude_md(self, *, budget_profile: str = "standard") -> str:
        ctx = self.assemble(budget_profile=budget_profile)
        state = self._state.state

        sections = [
            "# CLAUDE.md (Dynamic — Generated by SuperOPC Context Assembler)\n",
            f"## Current State: {state.status.value}\n",
            f"**Project:** {state.project_name}",
            f"**Focus:** {state.current_focus}",
            f"**Phase:** {state.phase_name or state.status.value}\n",
        ]

        sections.append("## Behavior Protocol\n")
        for rule in ctx["behavior_protocol"]:
            sections.append(f"- {rule}")
        sections.append("")

        sections.append("## Active Skills (Priority Order)\n")
        for skill in ctx["skills"]:
            sections.append(f"- `{skill}`")
        sections.append("")

        sections.append("## Active Agents\n")
        for agent in ctx["agents"]:
            sections.append(f"- `{agent}`")
        sections.append("")

        if ctx["rules"]:
            sections.append("## Active Rules\n")
            for rule in ctx["rules"]:
                sections.append(f"- `{rule}`")
            sections.append("")

        if ctx["learnings"]:
            sections.append("## Relevant Learnings\n")
            for learning in ctx["learnings"]:
                sections.append(f"- [{learning['category']}] {learning['title']}: {learning['content'][:100]}...")
            sections.append("")

        if ctx["methodologies"]:
            sections.append("## Relevant Methodologies\n")
            for methodology in ctx["methodologies"]:
                sections.append(
                    f"- {methodology['name']} ({methodology['domain']}): {methodology['one_liner']}"
                )
            sections.append("")

        if ctx["extracted_skills"]:
            sections.append("## External Pattern Learnings\n")
            for skill in ctx["extracted_skills"]:
                lessons = "; ".join(skill.get("lessons", [])[:2])
                summary = lessons or ", ".join(skill.get("architecture_hints", [])[:2]) or "stored pattern"
                sections.append(f"- {skill['repo']}: {summary}")
            sections.append("")

        dev = ctx.get("developer_profile", {}).get("developer_profile", {})
        if dev:
            sections.append("## Developer Preferences\n")
            sections.append(f"- Communication: {dev.get('style', 'balanced')}")
            sections.append(f"- Explanation depth: {dev.get('depth', 'moderate')}")
            sections.append(f"- Decision style: {dev.get('decision', 'analytical')}")
            sections.append("")

        return "\n".join(sections)

    # -- Selection helpers --

    def _select_skills(self, phase: ProjectPhase, task_hint: str) -> list[str]:
        priority = list(PHASE_SKILL_PRIORITY.get(phase, []))

        if task_hint:
            hint_lower = task_hint.lower()
            if "test" in hint_lower or "tdd" in hint_lower:
                self._promote(priority, "tdd")
            if "debug" in hint_lower:
                self._promote(priority, "debugging")
            if "api" in hint_lower:
                self._promote(priority, "implementing")
            if "seo" in hint_lower:
                self._promote(priority, "business-advisory")
            if "price" in hint_lower or "pricing" in hint_lower:
                self._promote(priority, "business-advisory")

        return priority[:10]

    def _select_agents(self, phase: ProjectPhase, task_hint: str) -> list[str]:
        return PHASE_AGENT_PRIORITY.get(phase, ["opc-orchestrator"])[:6]

    def _select_rules(self, phase: ProjectPhase) -> list[str]:
        rules = list(PHASE_RULES_PRIORITY.get(phase, ["coding-style", "git-workflow"]))
        personal_dir = self._root / "rules" / "personal"
        if personal_dir.is_dir():
            for md_file in sorted(personal_dir.glob("*.md")):
                rules.append(f"personal/{md_file.stem}")
        return rules

    def _select_references(self, phase: ProjectPhase) -> list[str]:
        refs = list(PHASE_REFERENCE_PRIORITY.get(phase, ["gates", "anti-patterns", "context-budget"]))
        return refs

    def _select_learnings(self, state: ProjectState, task_hint: str) -> list[dict[str, Any]]:
        tags = state.current_focus.lower().split() if state.current_focus else []
        if task_hint:
            tags.extend(task_hint.lower().split())
        return self._learnings.get_context_injection(tags=tags or None, limit=5)

    def _select_methodologies(
        self,
        phase: ProjectPhase,
        state: ProjectState,
        task_hint: str,
    ) -> list[dict[str, Any]]:
        terms = self._context_terms(state.current_focus, task_hint)
        if terms:
            tagged = self._methodologies.get_context_injection(tags=terms[:5], limit=3)
            if tagged:
                return tagged

        domain = self._preferred_methodology_domain(phase, task_hint)
        if domain:
            by_domain = self._methodologies.get_context_injection(domain=domain, limit=3)
            if by_domain:
                return by_domain

        return self._methodologies.get_context_injection(limit=3)

    def _select_extracted_skills(self, state: ProjectState, task_hint: str) -> list[dict[str, Any]]:
        output_dir = self._root / ".opc" / "intelligence" / "extracted-skills"
        if not output_dir.is_dir():
            return []

        terms = self._context_terms(state.current_focus, task_hint)
        candidates: list[tuple[int, float, dict[str, Any]]] = []
        for json_file in output_dir.glob("*.json"):
            try:
                payload = json.loads(json_file.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                continue
            score = self._score_extracted_skill(payload, terms)
            candidates.append((score, json_file.stat().st_mtime, payload))

        candidates.sort(key=lambda item: (item[0], item[1]), reverse=True)
        return [self._summarize_extracted_skill(payload) for _, _, payload in candidates[:3]]

    def _state_summary(self, state: ProjectState) -> dict[str, Any]:
        return {
            "phase": state.status.value,
            "focus": state.current_focus,
            "blockers": len(state.blockers),
            "todos": len(state.todos),
            "validation_debt": len(state.validation_debt),
        }

    def _behavior_protocol(self, phase: ProjectPhase) -> list[str]:
        rules = [
            "[Superpowers] SKILL-FIRST: If a relevant skill exists, invoke it — even with 1% applicability.",
            "[GSD] CONTEXT-DECAY-DEFENSE: Monitor context budget; degrade gracefully at 80% usage.",
            "[ECC] CONTINUOUS-LEARNING: After every session, capture insights to ~/.opc/learnings/.",
            "[Minimalist Entrepreneur] ANTI-BUILD-TRAP: No code generation without validate-idea + find-community evidence.",
        ]

        if phase == ProjectPhase.EXECUTING:
            rules.extend([
                "[Superpowers] TDD-IRON-LAW: No production code without a failing test first.",
                "[GSD] WAVE-EXECUTION: Parallelize independent tasks; serialize dependent ones.",
                "[Claude Code Best Practice] ATOMIC-COMMITS: One task = one commit.",
            ])
        elif phase == ProjectPhase.PLANNING:
            rules.extend([
                "[Agency-Agents] NEXUS-PROTOCOL: Consult specialist agents for domain-specific planning.",
                "[skill-from-masters] METHODOLOGY-FIRST: Align plan with proven expert methodologies.",
            ])
        elif phase in (ProjectPhase.IDLE, ProjectPhase.DISCUSSING):
            rules.extend([
                "[Follow Builders] BUILDER-INTEL: Check builder feeds before validation.",
                "[last30days] MULTI-SOURCE: Use multiple data sources for market assessment.",
            ])

        return rules

    @staticmethod
    def _promote(lst: list[str], item: str) -> None:
        if item in lst:
            lst.remove(item)
        lst.insert(0, item)

    @staticmethod
    def _context_terms(*texts: str) -> list[str]:
        terms: list[str] = []
        for text in texts:
            if not text:
                continue
            for token in re.findall(r"[a-z0-9][a-z0-9+._-]{2,}", text.lower()):
                terms.append(token)
        return list(dict.fromkeys(terms))

    @staticmethod
    def _preferred_methodology_domain(phase: ProjectPhase, task_hint: str) -> str:
        hint = task_hint.lower()
        if "pricing" in hint or "price" in hint:
            return "pricing"
        if "growth" in hint or "seo" in hint or "launch" in hint:
            return "growth"
        if "test" in hint or "tdd" in hint or "refactor" in hint or "api" in hint:
            return "engineering"
        if phase in (ProjectPhase.IDLE, ProjectPhase.DISCUSSING):
            return "validation"
        if phase == ProjectPhase.PLANNING:
            return "product"
        if phase == ProjectPhase.EXECUTING:
            return "engineering"
        if phase == ProjectPhase.SHIPPING:
            return "growth"
        return ""

    @staticmethod
    def _score_extracted_skill(payload: dict[str, Any], terms: list[str]) -> int:
        if not terms:
            return 0
        haystack = " ".join(
            [
                payload.get("repo", ""),
                payload.get("description", ""),
                " ".join(payload.get("tech_stack", [])),
                " ".join(payload.get("architecture_hints", [])),
                " ".join(payload.get("testing_patterns", [])),
                " ".join(payload.get("lessons", [])),
            ]
        ).lower()
        return sum(1 for term in terms if term in haystack)

    @staticmethod
    def _summarize_extracted_skill(payload: dict[str, Any]) -> dict[str, Any]:
        return {
            "repo": payload.get("repo", ""),
            "tech_stack": payload.get("tech_stack", [])[:5],
            "architecture_hints": payload.get("architecture_hints", [])[:5],
            "testing_patterns": payload.get("testing_patterns", [])[:4],
            "ci_patterns": payload.get("ci_patterns", [])[:4],
            "lessons": payload.get("lessons", [])[:3],
        }
