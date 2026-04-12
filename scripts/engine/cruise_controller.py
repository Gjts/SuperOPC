#!/usr/bin/env python3
"""
cruise_controller.py — Autonomous cruise mode for SuperOPC v2.

Three operating modes:
  - Watch:  Monitor only, notify on anomalies
  - Assist: Execute GREEN zone tasks, pause on YELLOW/RED
  - Cruise: Execute GREEN + YELLOW tasks, pause only on RED

The controller runs a heartbeat loop that:
  1. Reads current state
  2. Runs health check
  3. Asks the decision engine for next action
  4. Checks the action's permission zone
  5. Executes or escalates accordingly
  6. Updates state and logs
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from event_bus import EventBus, get_event_bus
from state_engine import StateEngine, get_state_engine
from decision_engine import ActionZone, Decision, DecisionEngine
from notification import NotificationDispatcher


# ---------------------------------------------------------------------------
# Cruise modes
# ---------------------------------------------------------------------------

class CruiseMode(str, Enum):
    WATCH = "watch"
    ASSIST = "assist"
    CRUISE = "cruise"


@dataclass
class CruiseStatus:
    mode: CruiseMode = CruiseMode.WATCH
    running: bool = False
    heartbeat_count: int = 0
    actions_executed: int = 0
    actions_skipped: int = 0
    actions_escalated: int = 0
    last_heartbeat: str = ""
    last_decision: dict[str, Any] = field(default_factory=dict)
    started_at: str = ""
    errors: list[str] = field(default_factory=list)
    consecutive_failures: int = 0


# ---------------------------------------------------------------------------
# CruiseController
# ---------------------------------------------------------------------------

class CruiseController:
    """Autonomous operation controller with zone-based permission checks."""

    MAX_CONSECUTIVE_FAILURES = 3
    DEFAULT_HEARTBEAT_SECONDS = 60

    def __init__(
        self,
        opc_dir: Path,
        *,
        mode: CruiseMode = CruiseMode.WATCH,
        heartbeat_seconds: int = 60,
        bus: EventBus | None = None,
    ):
        self._opc_dir = opc_dir
        self._bus = bus or get_event_bus(opc_dir / "events")
        self._state_engine = get_state_engine(opc_dir, self._bus)
        self._decision_engine = DecisionEngine(self._state_engine, self._bus)
        self._notifier = NotificationDispatcher(opc_dir, self._bus)
        self._heartbeat_seconds = heartbeat_seconds
        self._status = CruiseStatus(mode=mode)
        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._log_dir = opc_dir / "cruise-log"

    @property
    def status(self) -> CruiseStatus:
        return self._status

    def start(self, *, hours: float = 0) -> None:
        if self._status.running:
            return

        self._status.running = True
        self._status.started_at = _now()
        self._status.consecutive_failures = 0
        self._stop_event.clear()

        self._bus.publish("cruise.start", {"mode": self._status.mode.value, "hours": hours}, source="cruise_controller")
        self._notifier.notify(
            "Cruise Mode Started",
            f"Mode: {self._status.mode.value} | Heartbeat: {self._heartbeat_seconds}s" + (f" | Duration: {hours}h" if hours else ""),
            level="info",
        )

        self._thread = threading.Thread(target=self._loop, args=(hours,), daemon=True, name="opc-cruise")
        self._thread.start()

    def stop(self, reason: str = "manual") -> None:
        self._status.running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=10)
            self._thread = None

        self._bus.publish("cruise.stop", {"reason": reason, "heartbeats": self._status.heartbeat_count}, source="cruise_controller")
        self._notifier.notify("Cruise Mode Stopped", f"Reason: {reason} | Heartbeats: {self._status.heartbeat_count}", level="info")
        self._persist_status()

    def _loop(self, hours: float) -> None:
        deadline = time.time() + hours * 3600 if hours > 0 else float("inf")

        while self._status.running and time.time() < deadline:
            try:
                self._heartbeat()
            except Exception as exc:
                self._status.errors.append(f"{_now()}: {exc}")
                self._status.consecutive_failures += 1
                if self._status.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    self._emergency_stop(str(exc))
                    return

            self._stop_event.wait(timeout=self._heartbeat_seconds)
            if self._stop_event.is_set():
                break

        if self._status.running:
            self.stop(reason="duration_expired" if hours > 0 else "loop_exit")

    def _heartbeat(self) -> None:
        self._status.heartbeat_count += 1
        self._status.last_heartbeat = _now()

        self._state_engine.load()
        state = self._state_engine.state

        context = self._build_context()
        decision = self._decision_engine.decide(context)
        self._status.last_decision = decision.to_dict()

        self._bus.publish("cruise.heartbeat", {
            "count": self._status.heartbeat_count,
            "decision": decision.command,
            "zone": decision.zone.value,
        }, source="cruise_controller")

        allowed = self._check_zone(decision)

        if allowed:
            self._execute_decision(decision)
            self._status.actions_executed += 1
            self._status.consecutive_failures = 0
        elif decision.zone == ActionZone.RED:
            self._status.actions_escalated += 1
            self._notifier.notify(
                f"[RED ZONE] Approval Required: {decision.command}",
                f"Reason: {decision.reason}\nAction: {decision.action.value}",
                level="warning",
                metadata=decision.to_dict(),
            )
        else:
            self._status.actions_skipped += 1

        self._persist_status()

    def _check_zone(self, decision: Decision) -> bool:
        zone = decision.zone
        mode = self._status.mode

        if zone == ActionZone.GREEN:
            return True
        if zone == ActionZone.YELLOW and mode == CruiseMode.CRUISE:
            return True
        if zone == ActionZone.YELLOW and mode == CruiseMode.ASSIST:
            return False
        return False

    def _execute_decision(self, decision: Decision) -> None:
        self._log_decision(decision, executed=True)

    def _emergency_stop(self, error: str) -> None:
        self._notifier.notify(
            "CRUISE EMERGENCY STOP",
            f"{self.MAX_CONSECUTIVE_FAILURES} consecutive failures. Last error: {error}",
            level="critical",
        )
        self.stop(reason=f"emergency: {error[:100]}")

    def _build_context(self) -> dict[str, Any]:
        ctx: dict[str, Any] = {}

        handoff_file = self._opc_dir / "HANDOFF.json"
        ctx["handoff_exists"] = handoff_file.exists()

        intel_dir = self._opc_dir / "intelligence"
        if intel_dir.exists():
            ctx["has_intel"] = True

        return ctx

    def _log_decision(self, decision: Decision, *, executed: bool) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        date_str = _now()[:10]
        log_file = self._log_dir / f"cruise-{date_str}.jsonl"
        entry = {
            "timestamp": _now(),
            "heartbeat": self._status.heartbeat_count,
            "decision": decision.to_dict(),
            "executed": executed,
            "mode": self._status.mode.value,
        }
        with open(log_file, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False) + "\n")

    def _persist_status(self) -> None:
        self._log_dir.mkdir(parents=True, exist_ok=True)
        status_file = self._log_dir / "status.json"
        data = asdict(self._status)
        data["mode"] = self._status.mode.value
        status_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def get_summary(self) -> dict[str, Any]:
        s = self._status
        return {
            "mode": s.mode.value,
            "running": s.running,
            "heartbeats": s.heartbeat_count,
            "executed": s.actions_executed,
            "skipped": s.actions_skipped,
            "escalated": s.actions_escalated,
            "last_heartbeat": s.last_heartbeat,
            "last_decision": s.last_decision,
            "started_at": s.started_at,
            "errors_count": len(s.errors),
        }


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
