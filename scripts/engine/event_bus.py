#!/usr/bin/env python3
"""
event_bus.py — The central nervous system of SuperOPC v2.

Lightweight publish/subscribe event bus that unifies all internal
communication.  Supports both synchronous and asynchronous subscribers,
persistent event journaling to `.opc/events/`, and wildcard topic matching.
"""

from __future__ import annotations

import json
import threading
import time
import uuid
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Protocol


# ---------------------------------------------------------------------------
# Event definitions
# ---------------------------------------------------------------------------

CORE_EVENTS = frozenset({
    "project.init",
    "phase.start",
    "phase.complete",
    "task.assigned",
    "task.complete",
    "task.failed",
    "task.retry",
    "quality.check",
    "quality.violation",
    "quality.passed",
    "git.commit",
    "git.push",
    "schedule.tick",
    "market.update",
    "session.start",
    "session.end",
    "decision.required",
    "decision.made",
    "autonomous.proceed",
    "autonomous.blocked",
    "cruise.heartbeat",
    "cruise.start",
    "cruise.stop",
    "notification.send",
    "learning.captured",
    "profile.updated",
})


@dataclass(frozen=True)
class Event:
    topic: str
    payload: dict[str, Any] = field(default_factory=dict)
    event_id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    timestamp: str = field(
        default_factory=lambda: (
            datetime.now(timezone.utc)
            .replace(microsecond=0)
            .isoformat()
            .replace("+00:00", "Z")
        ),
    )
    source: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class Subscriber(Protocol):
    def __call__(self, event: Event) -> None: ...


# ---------------------------------------------------------------------------
# EventBus
# ---------------------------------------------------------------------------

class EventBus:
    """Thread-safe publish/subscribe event bus with optional journaling."""

    def __init__(self, *, journal_dir: Path | None = None, max_history: int = 500):
        self._subscribers: dict[str, list[Callable[[Event], None]]] = defaultdict(list)
        self._lock = threading.Lock()
        self._history: list[Event] = []
        self._max_history = max_history
        self._journal_dir = journal_dir
        if journal_dir:
            journal_dir.mkdir(parents=True, exist_ok=True)

    def subscribe(self, topic: str, callback: Callable[[Event], None]) -> None:
        with self._lock:
            self._subscribers[topic].append(callback)

    def unsubscribe(self, topic: str, callback: Callable[[Event], None]) -> None:
        with self._lock:
            subs = self._subscribers.get(topic, [])
            self._subscribers[topic] = [s for s in subs if s is not callback]

    def publish(self, topic: str, payload: dict[str, Any] | None = None, *, source: str = "") -> Event:
        event = Event(topic=topic, payload=payload or {}, source=source)
        self._record(event)
        self._dispatch(event)
        return event

    def emit(self, event: Event) -> None:
        self._record(event)
        self._dispatch(event)

    def _dispatch(self, event: Event) -> None:
        with self._lock:
            exact = list(self._subscribers.get(event.topic, []))
            wildcard = list(self._subscribers.get("*", []))

        for callback in exact + wildcard:
            try:
                callback(event)
            except Exception as exc:
                import sys
                print(f"[EventBus] subscriber error on {event.topic}: {exc}", file=sys.stderr)

    def _record(self, event: Event) -> None:
        with self._lock:
            self._history.append(event)
            if len(self._history) > self._max_history:
                self._history = self._history[-self._max_history:]

        if self._journal_dir:
            self._journal_event(event)

    def _journal_event(self, event: Event) -> None:
        try:
            date_str = event.timestamp[:10]
            journal_file = self._journal_dir / f"events-{date_str}.jsonl"
            line = json.dumps(event.to_dict(), ensure_ascii=False) + "\n"
            with open(journal_file, "a", encoding="utf-8") as fh:
                fh.write(line)
        except OSError:
            pass

    @property
    def history(self) -> list[Event]:
        with self._lock:
            return list(self._history)

    def recent(self, n: int = 20, *, topic: str | None = None) -> list[Event]:
        with self._lock:
            source = self._history
        if topic:
            source = [e for e in source if e.topic == topic or e.topic.startswith(topic + ".")]
        return source[-n:]

    def clear_history(self) -> None:
        with self._lock:
            self._history.clear()


# ---------------------------------------------------------------------------
# Singleton
# ---------------------------------------------------------------------------

_global_bus: EventBus | None = None
_bus_lock = threading.Lock()


def get_event_bus(journal_dir: Path | None = None) -> EventBus:
    global _global_bus
    with _bus_lock:
        if _global_bus is None:
            _global_bus = EventBus(journal_dir=journal_dir)
        return _global_bus


def reset_event_bus() -> None:
    global _global_bus
    with _bus_lock:
        _global_bus = None
