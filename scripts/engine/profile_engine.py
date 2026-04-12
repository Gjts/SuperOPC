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

    @staticmethod
    def _dict_to_profile(data: dict[str, Any]) -> DeveloperProfile:
        known_fields = {f.name for f in DeveloperProfile.__dataclass_fields__.values()}
        filtered = {k: v for k, v in data.items() if k in known_fields}
        return DeveloperProfile(**filtered)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
