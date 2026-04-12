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

from event_bus import EventBus, get_event_bus


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

    def stats(self) -> dict[str, Any]:
        self._ensure_loaded()
        by_category: dict[str, int] = {}
        for learning in self._index.values():
            by_category[learning.category] = by_category.get(learning.category, 0) + 1
        return {
            "total": len(self._index),
            "by_category": by_category,
            "store_dir": str(self._dir),
        }

    def _persist(self, learning: Learning) -> None:
        cat_dir = self._dir / learning.category
        cat_dir.mkdir(parents=True, exist_ok=True)
        filepath = cat_dir / f"{learning.id}.json"
        learning.updated_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
        filepath.write_text(json.dumps(asdict(learning), ensure_ascii=False, indent=2), encoding="utf-8")

    @staticmethod
    def _dict_to_learning(data: dict[str, Any]) -> Learning:
        known = {f.name for f in Learning.__dataclass_fields__.values()}
        return Learning(**{k: v for k, v in data.items() if k in known})
