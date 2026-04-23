#!/usr/bin/env python3
"""
learning_store.py — Cross-session, cross-project knowledge persistence for SuperOPC v2.

Stores four categories of learning:
  - Technical insights (best practices, gotchas per stack)
  - Project patterns (successful/failed architecture decisions)
  - Business rules (pricing experiments, channel effectiveness)
  - Debug experience (symptom → root-cause mappings)

All learnings are stored as JSON files in ~/.opc/learnings/ and are
automatically injected into the planner context at session start.
"""

from __future__ import annotations

import json
import re
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from engine.event_bus import EventBus, get_event_bus


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


# ---------------------------------------------------------------------------
# Learning model
# ---------------------------------------------------------------------------

class LearningCategory:
    TECHNICAL = "technical"
    PROJECT = "project"
    BUSINESS = "business"
    DEBUG = "debug"


@dataclass
class Learning:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:10])
    category: str = LearningCategory.TECHNICAL
    title: str = ""
    content: str = ""
    tags: list[str] = field(default_factory=list)
    source_project: str = ""
    confidence: float = 0.7
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )
    updated_at: str = ""
    access_count: int = 0


# ---------------------------------------------------------------------------
# LearningStore
# ---------------------------------------------------------------------------

class LearningStore:
    """Persistent knowledge base shared across all SuperOPC projects."""

    GLOBAL_DIR = Path.home() / ".opc" / "learnings"

    def __init__(self, *, store_dir: Path | None = None, bus: EventBus | None = None):
        self._dir = store_dir or self.GLOBAL_DIR
        self._bus = bus or get_event_bus()
        self._index: dict[str, Learning] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        self._dir.mkdir(parents=True, exist_ok=True)
        for cat_dir in self._dir.iterdir():
            if not cat_dir.is_dir():
                continue
            for filepath in cat_dir.glob("*.json"):
                try:
                    data = json.loads(filepath.read_text(encoding="utf-8"))
                    learning = self._dict_to_learning(data)
                    self._index[learning.id] = learning
                except (json.JSONDecodeError, OSError):
                    continue
        self._loaded = True

    def capture(self, *, category: str, title: str, content: str, tags: list[str] | None = None, source_project: str = "", confidence: float = 0.7) -> Learning:
        self._ensure_loaded()
        learning = Learning(
            category=category,
            title=title,
            content=content,
            tags=tags or [],
            source_project=source_project,
            confidence=confidence,
        )
        self._index[learning.id] = learning
        self._persist(learning)
        self._bus.publish("learning.captured", {"id": learning.id, "category": category, "title": title}, source="learning_store")
        return learning

    def query(self, *, category: str | None = None, tags: list[str] | None = None, keyword: str = "", limit: int = 20) -> list[Learning]:
        self._ensure_loaded()
        results: list[Learning] = []

        for learning in self._index.values():
            if category and learning.category != category:
                continue
            if tags and not any(t in learning.tags for t in tags):
                continue
            if keyword:
                keyword_lower = keyword.lower()
                searchable = f"{learning.title} {learning.content} {' '.join(learning.tags)}".lower()
                if keyword_lower not in searchable:
                    continue
            results.append(learning)

        results.sort(key=lambda l: (l.confidence, l.access_count), reverse=True)
        for r in results[:limit]:
            r.access_count += 1
        return results[:limit]

    def get_context_injection(self, *, tags: list[str] | None = None, limit: int = 10) -> list[dict[str, Any]]:
        relevant = self.query(tags=tags, limit=limit)
        return [
            {
                "title": l.title,
                "category": l.category,
                "content": l.content[:500],
                "confidence": l.confidence,
                "source": l.source_project,
            }
            for l in relevant
        ]

    def capture_from_session(self, session_data: dict[str, Any]) -> list[Learning]:
        captured: list[Learning] = []
        project = session_data.get("project", "")

        decisions = session_data.get("architecture_decisions", [])
        for decision in decisions:
            learning = self.capture(
                category=LearningCategory.PROJECT,
                title=f"Architecture: {decision.get('title', 'untitled')}",
                content=decision.get("rationale", ""),
                tags=decision.get("tags", []),
                source_project=project,
            )
            captured.append(learning)

        debug_sessions = session_data.get("debug_resolutions", [])
        for debug in debug_sessions:
            learning = self.capture(
                category=LearningCategory.DEBUG,
                title=f"Debug: {debug.get('symptom', 'unknown')}",
                content=f"Root cause: {debug.get('root_cause', 'unknown')}\nFix: {debug.get('fix', 'unknown')}",
                tags=debug.get("tags", ["debug"]),
                source_project=project,
                confidence=0.85,
            )
            captured.append(learning)

        return captured

    # ------------------------------------------------------------------
    # Observation pipeline (inspired by ECC Continuous Learning v2)
    # ------------------------------------------------------------------

    def record_observation(self, *, tool: str, action: str, context: str = "", project: str = "", metadata: dict[str, Any] | None = None) -> None:
        """Append a raw tool-use observation to the JSONL observation log."""
        obs_file = self._dir / "observations.jsonl"
        self._dir.mkdir(parents=True, exist_ok=True)
        record = {
            "ts": _now(),
            "tool": tool,
            "action": action,
            "context": context[:200],
            "project": project,
            "meta": metadata or {},
        }
        with open(obs_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def detect_patterns(self, *, min_occurrences: int = 3) -> list[dict[str, Any]]:
        """Analyze observations.jsonl to detect recurring tool-use patterns."""
        obs_file = self._dir / "observations.jsonl"
        if not obs_file.exists():
            return []

        action_counts: dict[str, int] = {}
        tool_counts: dict[str, int] = {}
        tool_action_pairs: dict[str, int] = {}

        for line in obs_file.read_text(encoding="utf-8").strip().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            tool = rec.get("tool", "")
            action = rec.get("action", "")
            if tool:
                tool_counts[tool] = tool_counts.get(tool, 0) + 1
            if action:
                action_counts[action] = action_counts.get(action, 0) + 1
            pair_key = f"{tool}:{action}"
            tool_action_pairs[pair_key] = tool_action_pairs.get(pair_key, 0) + 1

        patterns: list[dict[str, Any]] = []
        for pair, count in sorted(tool_action_pairs.items(), key=lambda x: -x[1]):
            if count >= min_occurrences:
                tool_name, action_name = pair.split(":", 1) if ":" in pair else (pair, "")
                patterns.append({
                    "type": "tool_action_pattern",
                    "tool": tool_name,
                    "action": action_name,
                    "count": count,
                    "strength": min(1.0, count / 20.0),
                })
        return patterns

    def evolve_instincts(self) -> list[Learning]:
        """Promote detected patterns into instincts (Learning entries with high confidence)."""
        patterns = self.detect_patterns(min_occurrences=5)
        instincts: list[Learning] = []
        for pattern in patterns:
            existing = self.query(
                category=LearningCategory.TECHNICAL,
                keyword=f"instinct:{pattern['tool']}:{pattern['action']}",
                limit=1,
            )
            if existing:
                continue
            instinct = self.capture(
                category=LearningCategory.TECHNICAL,
                title=f"instinct:{pattern['tool']}:{pattern['action']}",
                content=f"Recurring pattern detected: {pattern['tool']} used for '{pattern['action']}' "
                        f"({pattern['count']} occurrences). Consider creating a dedicated skill or command.",
                tags=["instinct", "auto-detected", pattern["tool"]],
                confidence=pattern["strength"],
            )
            instincts.append(instinct)
        if instincts:
            self._bus.publish(
                "learning.instincts_evolved",
                {"count": len(instincts), "patterns": len(patterns)},
                source="learning_store",
            )
        return instincts

    def prune_observations(self, *, max_age_days: int = 30) -> int:
        """Remove observations older than max_age_days. Returns count of pruned records."""
        obs_file = self._dir / "observations.jsonl"
        if not obs_file.exists():
            return 0
        cutoff = datetime.now(timezone.utc).replace(microsecond=0)
        kept: list[str] = []
        pruned = 0
        for line in obs_file.read_text(encoding="utf-8").strip().splitlines():
            try:
                rec = json.loads(line)
                ts_str = rec.get("ts", "")
                if ts_str:
                    ts = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
                    age = (cutoff - ts).days
                    if age > max_age_days:
                        pruned += 1
                        continue
            except (json.JSONDecodeError, ValueError):
                pass
            kept.append(line)
        obs_file.write_text("\n".join(kept) + ("\n" if kept else ""), encoding="utf-8")
        return pruned

    def stats(self) -> dict[str, Any]:
        self._ensure_loaded()
        by_category: dict[str, int] = {}
        for learning in self._index.values():
            by_category[learning.category] = by_category.get(learning.category, 0) + 1

        obs_count = 0
        obs_file = self._dir / "observations.jsonl"
        if obs_file.exists():
            obs_count = sum(1 for _ in obs_file.read_text(encoding="utf-8").strip().splitlines() if _)

        return {
            "total": len(self._index),
            "by_category": by_category,
            "observations": obs_count,
            "store_dir": str(self._dir),
        }

    def _persist(self, learning: Learning) -> None:
        cat_dir = self._dir / learning.category
        cat_dir.mkdir(parents=True, exist_ok=True)
        filepath = cat_dir / f"{learning.id}.json"
        learning.updated_at = _now()
        filepath.write_text(json.dumps(asdict(learning), ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _dict_to_learning(data: dict[str, Any]) -> Learning:
        known = {f.name for f in Learning.__dataclass_fields__.values()}
        return Learning(**{k: v for k, v in data.items() if k in known})
