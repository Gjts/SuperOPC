#!/usr/bin/env python3
"""
bridge.py — Hook-to-EventBus bridge for SuperOPC v2.

Provides a lightweight fire-and-forget interface that hook scripts
can call to emit events to the v2 engine's event bus.  Failures
are silently swallowed so hooks remain non-blocking.

Usage from any hook script:

    from bridge import emit_hook_event
    emit_hook_event("hook.commit_quality", {"message": msg, "status": "warn"})
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

ENGINE_DIR = Path(__file__).resolve().parent.parent / "engine"

_bus_initialized = False


def _ensure_engine_path() -> None:
    global _bus_initialized
    if _bus_initialized:
        return
    engine_path = str(ENGINE_DIR)
    if engine_path not in sys.path:
        sys.path.insert(0, engine_path)
    _bus_initialized = True


def emit_hook_event(topic: str, payload: dict[str, Any] | None = None, *, source: str = "hook") -> None:
    """Publish an event to the v2 event bus. Silently no-ops on failure."""
    try:
        _ensure_engine_path()
        from event_bus import get_event_bus
        opc_events_dir = _find_opc_events_dir()
        bus = get_event_bus(journal_dir=opc_events_dir)
        bus.publish(topic, payload or {}, source=source)
    except Exception:
        pass


def _find_opc_events_dir() -> Path | None:
    """Walk up from CWD to find .opc/events/ for journaling."""
    cwd = Path.cwd()
    for candidate in [cwd] + list(cwd.parents):
        events_dir = candidate / ".opc" / "events"
        if (candidate / ".opc").is_dir():
            events_dir.mkdir(parents=True, exist_ok=True)
            return events_dir
    return None
