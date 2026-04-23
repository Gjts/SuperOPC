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
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any

from engine.decision_engine import ActionType, ActionZone, Decision, DecisionEngine
from engine.event_bus import EventBus, get_event_bus
from engine.notification import NotificationDispatcher
from engine.state_engine import StateEngine, get_state_engine

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"

EXECUTION_TIMEOUT_SECONDS = 120
AGENT_EXECUTION_TIMEOUT_SECONDS = 600

# ---------------------------------------------------------------------------
# ActionType → Agent 映射
# ---------------------------------------------------------------------------
# 契约：凡是"真执行"类的 ActionType（YELLOW/RED 区），必须通过 agent workflow
# 派发，而不是脚本直调。这保证了 cruise 模式遵守 skill-first / agent-workflow 铁律。
#
# GREEN 区已实现的只读查询（HEALTH_CHECK / COLLECT_INTEL / RUN_TESTS）走
# read-only entrypoint，属于 autonomous-ops skill 明确的白名单例外。
# 未实现的 GREEN action 必须 fail closed，不能静默重定向到错误脚本。

ACTION_AGENT_MAP: dict[str, str] = {
    # ActionType.value → agent name
    "plan": "opc-planner",
    "build": "opc-executor",
    "review": "opc-reviewer",
    "debug": "opc-debugger",
    "ship": "opc-shipper",
    "research": "opc-researcher",
    "resume": "opc-session-manager",
    "pause": "opc-session-manager",
}

READ_ONLY_SCRIPT_MAP: dict[str, tuple[Path, list[str]]] = {
    # ActionType.value → (python entrypoint path, args template)
    "health_check": (REPO_ROOT / "scripts" / "opc_health.py", ["--target", "all"]),
    "collect_intel": (REPO_ROOT / "bin" / "opc-tools", ["--raw", "intel", "status"]),
    "run_tests": (REPO_ROOT / "bin" / "opc-tools", ["--raw", "verify", "health"]),
}


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
            result = self._execute_decision(decision)
            if result.get("success"):
                self._status.actions_executed += 1
                self._status.consecutive_failures = 0
            else:
                message = result.get("error") or result.get("stderr") or result.get("reason") or "decision dispatch failed"
                self._status.errors.append(f"{_now()}: {decision.action.value} failed — {message}")
                self._status.consecutive_failures += 1
                if self._status.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
                    self._emergency_stop(str(message))
                    return
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

    def _execute_decision(self, decision: Decision) -> dict[str, Any]:
        result = self._dispatch_command(decision)
        success = result.get("success", False)
        self._log_decision(decision, executed=success)

        self._bus.publish("cruise.executed", {
            "command": decision.command,
            "zone": decision.zone.value,
            "action": decision.action.value,
            "success": success,
            "heartbeat": self._status.heartbeat_count,
        }, source="cruise_controller")

        if decision.zone == ActionZone.YELLOW:
            self._notifier.notify(
                f"[YELLOW] {'Executed' if success else 'Failed'}: {decision.command}",
                f"Reason: {decision.reason}\nResult: {'ok' if success else 'failed'}",
                level="info" if success else "warning",
                metadata=result,
            )
        elif not success:
            self._notifier.notify(
                f"[{decision.zone.value.upper()}] Failed: {decision.command}",
                f"Reason: {decision.reason}\nResult: {result.get('error') or result.get('reason') or 'failed'}",
                level="warning",
                metadata=result,
            )
        return result

    def _dispatch_command(self, decision: Decision) -> dict[str, Any]:
        """Route a decision through the skill-first / agent-workflow contract.

        契约（AGENTS.md）：
          - YELLOW/RED 执行类 ActionType → claude --agent <owner> 真派发 agent
          - GREEN 只读查询 ActionType → 白名单脚本（autonomous-ops GREEN zone 例外）
          - WAIT/DISCUSS → noop
        """
        action_value = decision.action.value

        if decision.action in (ActionType.WAIT, ActionType.DISCUSS):
            return {
                "success": True,
                "action": "noop",
                "reason": "No executable action for wait/discuss",
            }

        # 路径 1：真执行 → 派发 agent（skill-first 契约）
        agent_name = ACTION_AGENT_MAP.get(action_value)
        if agent_name:
            return self._run_claude_agent(agent_name, decision)

        # 路径 2：GREEN 区只读查询 → 白名单脚本
        script_entry = READ_ONLY_SCRIPT_MAP.get(action_value)
        if script_entry:
            script_path, extra_args = script_entry
            args = ["--cwd", str(self._opc_dir.parent)] + list(extra_args)
            return self._run_python_entrypoint(script_path, args)

        if decision.zone == ActionZone.GREEN:
            return {
                "success": False,
                "action": "unhandled",
                "command": decision.command,
                "reason": f"No read-only dispatch mapping for green-zone action '{action_value}'.",
            }

        return self._run_opc_fallback(decision.command)

    def _run_claude_agent(self, agent: str, decision: Decision) -> dict[str, Any]:
        """Dispatch to a real agent via `claude --print --agent` — skill-first 契约唯一合法路径。"""
        prompt = self._build_agent_prompt(agent, decision)

        self._bus.publish(
            "cruise.agent_dispatch",
            {
                "agent": agent,
                "action": decision.action.value,
                "zone": decision.zone.value,
                "command": decision.command,
                "heartbeat": self._status.heartbeat_count,
            },
            source="cruise_controller",
        )

        try:
            proc = subprocess.run(
                ["claude", "--print", "--agent", agent, prompt],
                capture_output=True,
                text=True,
                timeout=AGENT_EXECUTION_TIMEOUT_SECONDS,
                cwd=str(self._opc_dir.parent),
            )
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "agent": agent,
                "stdout": proc.stdout[:2000] if proc.stdout else "",
                "stderr": proc.stderr[:500] if proc.stderr else "",
                "dispatch_mode": "agent",
            }
        except FileNotFoundError:
            return {
                "success": False,
                "agent": agent,
                "error": "'claude' CLI not found — cannot dispatch agent. Install Claude Code or switch to watch mode.",
                "dispatch_mode": "agent",
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "agent": agent,
                "error": f"Agent {agent} timed out after {AGENT_EXECUTION_TIMEOUT_SECONDS}s",
                "dispatch_mode": "agent",
            }
        except Exception as exc:
            return {
                "success": False,
                "agent": agent,
                "error": str(exc)[:200],
                "dispatch_mode": "agent",
            }

    @staticmethod
    def _build_agent_prompt(agent: str, decision: Decision) -> str:
        """Construct a context-bounded prompt for agent dispatch in cruise mode."""
        sections = [
            "==== CRUISE MODE DISPATCH ====",
            f"You are dispatched as `{agent}` by SuperOPC cruise controller.",
            f"Zone: {decision.zone.value.upper()} | Action: {decision.action.value} | Confidence: {decision.confidence}",
            f"Trigger reason: {decision.reason}",
            f"Suggested command equivalent: {decision.command}",
            "",
            "Constraints:",
            "- Follow your agent's full workflow (read agents/<you>.md if unsure).",
            "- Respect all HARD-GATE entry conditions.",
            "- Emit a concise final summary suitable for a heartbeat log.",
            "- Do NOT wander outside your designated workflow.",
        ]
        if decision.context:
            sections.append(f"\nDecision context: {json.dumps(decision.context, ensure_ascii=False)[:800]}")
        return "\n".join(sections)

    def _run_python_entrypoint(self, entrypoint: Path, args: list[str]) -> dict[str, Any]:
        """Execute a Python entrypoint and capture its output."""
        if not entrypoint.exists():
            return {"success": False, "error": f"Entrypoint not found: {entrypoint}"}
        try:
            proc = subprocess.run(
                [sys.executable, str(entrypoint)] + args,
                capture_output=True,
                text=True,
                timeout=EXECUTION_TIMEOUT_SECONDS,
                cwd=str(self._opc_dir.parent),
            )
            return {
                "success": proc.returncode == 0,
                "returncode": proc.returncode,
                "stdout": proc.stdout[:2000] if proc.stdout else "",
                "stderr": proc.stderr[:500] if proc.stderr else "",
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": f"Timeout after {EXECUTION_TIMEOUT_SECONDS}s"}
        except Exception as exc:
            return {"success": False, "error": str(exc)[:200]}

    def _run_opc_fallback(self, command: str) -> dict[str, Any]:
        """Fallback: log that the command couldn't be dispatched."""
        return {
            "success": False,
            "action": "unhandled",
            "command": command,
            "reason": "No dispatch mapping for this command. Manual intervention required.",
        }

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

        state_json = self._opc_dir / "state.json"
        if state_json.exists():
            try:
                data = json.loads(state_json.read_text(encoding="utf-8"))
                if data.get("validation_debt"):
                    ctx["quality_violations"] = data["validation_debt"]
            except (json.JSONDecodeError, OSError):
                pass

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
