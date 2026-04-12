#!/usr/bin/env python3
"""
scheduler.py — Lightweight cron-like scheduler for SuperOPC v2.

Runs periodic tasks (health checks, market intel, session recovery) in a
background thread.  Zero external dependencies — uses only stdlib
threading + time.
"""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from event_bus import Event, EventBus, get_event_bus


# ---------------------------------------------------------------------------
# Job definition
# ---------------------------------------------------------------------------

@dataclass
class ScheduledJob:
    name: str
    interval_seconds: int
    callback: Callable[[], None]
    enabled: bool = True
    last_run: float = 0.0
    run_count: int = 0
    last_error: str = ""


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Background scheduler that fires periodic jobs and emits events."""

    def __init__(self, bus: EventBus | None = None):
        self._bus = bus or get_event_bus()
        self._jobs: dict[str, ScheduledJob] = {}
        self._lock = threading.Lock()
        self._running = False
        self._thread: threading.Thread | None = None
        self._stop_event = threading.Event()

    def add_job(self, name: str, interval_seconds: int, callback: Callable[[], None], *, enabled: bool = True) -> None:
        with self._lock:
            self._jobs[name] = ScheduledJob(
                name=name,
                interval_seconds=interval_seconds,
                callback=callback,
                enabled=enabled,
            )

    def remove_job(self, name: str) -> None:
        with self._lock:
            self._jobs.pop(name, None)

    def enable_job(self, name: str) -> None:
        with self._lock:
            if name in self._jobs:
                self._jobs[name].enabled = True

    def disable_job(self, name: str) -> None:
        with self._lock:
            if name in self._jobs:
                self._jobs[name].enabled = False

    def start(self) -> None:
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True, name="opc-scheduler")
        self._thread.start()
        self._bus.publish("schedule.tick", {"action": "scheduler_started"}, source="scheduler")

    def stop(self) -> None:
        self._running = False
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def jobs(self) -> dict[str, dict[str, Any]]:
        with self._lock:
            return {
                name: {
                    "interval": job.interval_seconds,
                    "enabled": job.enabled,
                    "run_count": job.run_count,
                    "last_run": datetime.fromtimestamp(job.last_run, tz=timezone.utc).isoformat() if job.last_run else "never",
                    "last_error": job.last_error,
                }
                for name, job in self._jobs.items()
            }

    def _loop(self) -> None:
        while self._running:
            now = time.time()
            with self._lock:
                jobs_snapshot = list(self._jobs.values())

            for job in jobs_snapshot:
                if not job.enabled:
                    continue
                if now - job.last_run < job.interval_seconds:
                    continue
                self._execute_job(job, now)

            self._stop_event.wait(timeout=1.0)

    def _execute_job(self, job: ScheduledJob, now: float) -> None:
        try:
            job.callback()
            job.last_run = now
            job.run_count += 1
            job.last_error = ""
            self._bus.publish(
                "schedule.tick",
                {"job": job.name, "status": "success", "run_count": job.run_count},
                source="scheduler",
            )
        except Exception as exc:
            job.last_run = now
            job.last_error = str(exc)
            self._bus.publish(
                "schedule.tick",
                {"job": job.name, "status": "error", "error": str(exc)},
                source="scheduler",
            )


# ---------------------------------------------------------------------------
# Built-in job factories
# ---------------------------------------------------------------------------

def _make_health_check(opc_dir: Path) -> Callable[[], None]:
    def _run() -> None:
        bus = get_event_bus()
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
            from opc_quality import collect_project_quality_report
            report = collect_project_quality_report(opc_dir.parent, repair=False)
            findings = report.get("findings", [])
            if findings:
                bus.publish("quality.violation", {"findings": findings[:10], "total": len(findings)}, source="scheduler.health")
            else:
                bus.publish("quality.passed", {"message": "Health check passed"}, source="scheduler.health")
        except Exception as exc:
            bus.publish("quality.check", {"error": str(exc)}, source="scheduler.health")
    return _run


def _make_market_intel(opc_dir: Path, query: str) -> Callable[[], None]:
    def _run() -> None:
        bus = get_event_bus()
        try:
            import sys
            sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "intelligence"))
            from feed_scraper import compose_intelligence_report
            compose_intelligence_report(query)
            bus.publish("market.update", {"query": query, "status": "complete"}, source="scheduler.intel")
        except Exception as exc:
            bus.publish("market.update", {"query": query, "error": str(exc)}, source="scheduler.intel")
    return _run


def _make_session_recovery(opc_dir: Path) -> Callable[[], None]:
    def _run() -> None:
        bus = get_event_bus()
        handoff_file = opc_dir / "HANDOFF.json"
        if handoff_file.exists():
            try:
                data = json.loads(handoff_file.read_text(encoding="utf-8"))
                bus.publish("session.start", {"recovered_from": "HANDOFF.json", "handoff": data}, source="scheduler.recovery")
            except Exception:
                pass
    return _run


def create_default_scheduler(opc_dir: Path, *, market_query: str = "") -> Scheduler:
    bus = get_event_bus(opc_dir / "events")
    scheduler = Scheduler(bus=bus)

    scheduler.add_job("health_check", interval_seconds=86400, callback=_make_health_check(opc_dir))
    if market_query:
        scheduler.add_job("market_intel", interval_seconds=604800, callback=_make_market_intel(opc_dir, market_query))
    scheduler.add_job("session_recovery", interval_seconds=3600, callback=_make_session_recovery(opc_dir))

    return scheduler
