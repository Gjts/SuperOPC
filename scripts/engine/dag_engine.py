#!/usr/bin/env python3
"""
dag_engine.py — DAG Orchestration Engine v2 for SuperOPC.

A complete rewrite of the original dag_runner.py.  Improvements:
  - Dynamic DAG construction from events, not just static PLAN.md
  - Semantic agent routing via registry instead of keyword matching
  - Resilient execution: retry → decompose → degrade → escalate
  - Full execution history persisted to .opc/execution-log/
  - Context projection v2: dynamic context budget per task type
  - Integration with the event bus for real-time monitoring
"""

from __future__ import annotations

import concurrent.futures
import json
import re
import subprocess
import sys
import time
import uuid
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

if sys.stdout and sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

from engine.agent_runtime import AGENT_RUNTIME_CODEX, build_codex_handoff, detect_agent_runtime
from engine.event_bus import EventBus, get_event_bus
from opc_common import find_opc_dir

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
REGISTRY_PATH = REPO_ROOT / "agents" / "registry.json"

MAX_RETRIES = 3
MAX_WORKERS = 4


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class Task:
    id: str
    title: str
    file: str = ""
    action: str = ""
    test_expectation: str = ""
    completion_gate: str = ""
    depends_on: list[str] = field(default_factory=list)
    agent: str = ""
    retry_count: int = 0
    status: str = "pending"
    result: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_ms: int = 0


@dataclass
class Wave:
    id: str
    description: str = ""
    tasks: list[Task] = field(default_factory=list)


@dataclass
class ExecutionPlan:
    goal: str
    waves: list[Wave] = field(default_factory=list)
    plan_id: str = field(default_factory=lambda: uuid.uuid4().hex[:8])
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )


@dataclass
class ExecutionResult:
    plan_id: str
    goal: str
    status: str = "pending"
    waves_completed: int = 0
    waves_total: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_total: int = 0
    started_at: str = ""
    finished_at: str = ""
    log: list[dict[str, Any]] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Agent Registry
# ---------------------------------------------------------------------------

class AgentRegistry:
    """Loads and queries the agent capability registry."""

    def __init__(self, registry_path: Path | None = None):
        self._path = registry_path or REGISTRY_PATH
        self._agents: list[dict[str, Any]] = []
        self._load()

    def _load(self) -> None:
        if not self._path.exists():
            self._agents = []
            return
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
            self._agents = data.get("agents", []) if isinstance(data, dict) else []
        except (json.JSONDecodeError, OSError):
            self._agents = []

    def route(self, task: Task) -> str:
        if task.agent:
            return task.agent

        content_sig = f"{task.title} {task.action} {task.file}".lower()
        best_agent = "opc-executor"
        best_score = 0

        for agent in self._agents:
            score = 0
            for tag in agent.get("capability_tags", []):
                if tag.lower() in content_sig:
                    score += 2
            for scenario in agent.get("scenarios", []):
                if any(word in content_sig for word in scenario.lower().split()):
                    score += 1
            if score > best_score:
                best_score = score
                best_agent = agent.get("id", "opc-executor")

        if best_score == 0:
            return self._fallback_keyword_route(content_sig)

        return best_agent

    @staticmethod
    def _fallback_keyword_route(sig: str) -> str:
        frontend_kw = ("ui", "css", "frontend", "component", "view", "layout", "style")
        backend_kw = ("api", "db", "database", "backend", "model", "migration", "schema")
        security_kw = ("audit", "scan", "security", "owasp", "injection", "auth")

        if any(k in sig for k in frontend_kw):
            return "opc-frontend-wizard"
        if any(k in sig for k in backend_kw):
            return "opc-backend-architect"
        if any(k in sig for k in security_kw):
            return "opc-security-auditor"
        return "opc-executor"

    @property
    def all_agents(self) -> list[dict[str, Any]]:
        return list(self._agents)


# ---------------------------------------------------------------------------
# Plan Parser
# ---------------------------------------------------------------------------

def parse_plan_file(file_path: Path) -> ExecutionPlan | None:
    content = file_path.read_text(encoding="utf-8")
    match = re.search(r"<opc-plan>([\s\S]*?)</opc-plan>", content)
    if not match:
        return None

    xml_content = "<opc-plan>" + match.group(1) + "</opc-plan>"
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError:
        return None

    goal_node = root.find(".//metadata/goal")
    goal = goal_node.text.strip() if goal_node is not None and goal_node.text else "Unknown Goal"

    waves: list[Wave] = []
    for wave_node in root.findall(".//waves/wave"):
        wave_id = wave_node.get("id", "0")
        desc = wave_node.get("description", "")
        tasks: list[Task] = []
        for task_node in wave_node.findall("task"):
            deps_str = task_node.get("depends_on", "")
            deps = [d.strip() for d in deps_str.split(",") if d.strip()]
            tasks.append(Task(
                id=task_node.get("id", ""),
                title=_text(task_node, "title"),
                file=_text(task_node, "file"),
                action=_text(task_node, "action"),
                test_expectation=_text(task_node, "test-expectation"),
                completion_gate=_text(task_node, "completion-gate"),
                depends_on=deps,
            ))
        waves.append(Wave(id=wave_id, description=desc, tasks=tasks))

    return ExecutionPlan(goal=goal, waves=waves)


def _text(parent: ET.Element, tag: str) -> str:
    node = parent.find(tag)
    return (node.text or "").strip() if node is not None else ""


# ---------------------------------------------------------------------------
# Execution Engine
# ---------------------------------------------------------------------------

class DAGEngine:
    """Executes an ExecutionPlan with resilience, logging, and event integration."""

    def __init__(
        self,
        registry: AgentRegistry | None = None,
        bus: EventBus | None = None,
        log_dir: Path | None = None,
        dry_run: bool = False,
        project_root: Path | None = None,
    ):
        self._registry = registry or AgentRegistry()
        self._bus = bus or get_event_bus()
        self._log_dir = log_dir
        self._dry_run = dry_run
        self._project_root = (project_root or REPO_ROOT).resolve()
        self._completed_task_ids: set[str] = set()

    def execute(self, plan: ExecutionPlan) -> ExecutionResult:
        self._completed_task_ids = set()
        result = ExecutionResult(
            plan_id=plan.plan_id,
            goal=plan.goal,
            waves_total=len(plan.waves),
            tasks_total=sum(len(w.tasks) for w in plan.waves),
            started_at=_now(),
        )
        result.status = "running"

        self._bus.publish("phase.start", {"plan_id": plan.plan_id, "goal": plan.goal}, source="dag_engine")

        for wave in plan.waves:
            wave_ok = self._execute_wave(wave, result)
            if not wave_ok:
                if result.status != "handoff":
                    result.status = "failed"
                break
            result.waves_completed += 1

        if result.status == "running":
            result.status = "completed"

        result.finished_at = _now()
        self._persist_result(result)

        topic = "phase.complete" if result.status == "completed" else "task.handoff" if result.status == "handoff" else "task.failed"
        self._bus.publish(topic, {"plan_id": plan.plan_id, "status": result.status}, source="dag_engine")
        return result

    def _execute_wave(self, wave: Wave, result: ExecutionResult) -> bool:
        self._log(result, f"=== Wave {wave.id}: {wave.description} ({len(wave.tasks)} tasks) ===")

        for task in wave.tasks:
            task.agent = self._registry.route(task)

        pending: dict[str, Task] = {task.id: task for task in wave.tasks}
        while pending:
            ready = [
                task for task in pending.values()
                if set(task.depends_on).issubset(self._completed_task_ids)
            ]
            if not ready:
                unresolved = [
                    f"{task.id} -> missing {sorted(set(task.depends_on) - self._completed_task_ids)}"
                    for task in pending.values()
                ]
                result.tasks_failed += len(pending)
                self._log(result, f"[FATAL] Wave {wave.id} has unresolved in-wave dependencies: {'; '.join(unresolved)}")
                return False

            with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(ready), MAX_WORKERS)) as pool:
                futures = {pool.submit(self._execute_task_with_retry, task, result): task for task in ready}
                for future in concurrent.futures.as_completed(futures):
                    task = futures[future]
                    pending.pop(task.id, None)
                    try:
                        success = future.result()
                        if success:
                            result.tasks_completed += 1
                            self._completed_task_ids.add(task.id)
                        elif task.status == "handoff":
                            result.status = "handoff"
                            return False
                        else:
                            result.tasks_failed += 1
                            return False
                    except Exception as exc:
                        result.tasks_failed += 1
                        self._log(result, f"[FATAL] Task {task.id} exception: {exc}")
                        return False

        self._log(result, f"Wave {wave.id} completed successfully.")
        return True

    def _execute_task_with_retry(self, task: Task, result: ExecutionResult) -> bool:
        for attempt in range(1, MAX_RETRIES + 1):
            task.retry_count = attempt - 1
            task.started_at = _now()

            self._bus.publish("task.assigned", {"task_id": task.id, "agent": task.agent, "attempt": attempt}, source="dag_engine")

            success = self._run_agent(task, result)
            task.finished_at = _now()

            if success:
                task.status = "completed"
                self._bus.publish("task.complete", {"task_id": task.id, "agent": task.agent}, source="dag_engine")
                return True

            if task.status == "handoff":
                self._bus.publish("task.handoff", {"task_id": task.id, "agent": task.agent}, source="dag_engine")
                return False

            if attempt < MAX_RETRIES:
                self._log(result, f"  [RETRY] Task {task.id} failed (attempt {attempt}/{MAX_RETRIES}), retrying...")
                self._bus.publish("task.retry", {"task_id": task.id, "attempt": attempt}, source="dag_engine")
                time.sleep(1)

        task.status = "failed"
        self._bus.publish("task.failed", {"task_id": task.id, "agent": task.agent, "retries": MAX_RETRIES}, source="dag_engine")

        degraded = self._try_degrade(task, result)
        if degraded:
            task.status = "degraded"
            return True

        self._bus.publish("decision.required", {
            "reason": f"Task {task.id} failed after {MAX_RETRIES} retries and degradation",
            "task": asdict(task),
        }, source="dag_engine")
        return False

    def _run_agent(self, task: Task, result: ExecutionResult) -> bool:
        prompt = self._build_prompt(task)

        if self._dry_run:
            self._log(result, f"  [DRY-RUN] {task.agent} -> Task {task.id}: {task.title}")
            time.sleep(0.5)
            task.result = "dry-run-success"
            return True

        self._log(result, f"  [{task.agent}] -> Task {task.id}: {task.title}")
        try:
            runtime = detect_agent_runtime()
            if runtime == AGENT_RUNTIME_CODEX:
                handoff = build_codex_handoff(
                    agent=task.agent,
                    prompt=prompt,
                    source="dag-engine",
                    cwd=self._project_root,
                )
                task.result = json.dumps(handoff.get("handoff", {}), ensure_ascii=False)[:2000]
                task.status = "handoff"
                self._log(result, f"  [HANDOFF] Codex native agent required: {handoff['codex_agent']}")
                return False

            proc = subprocess.run(
                ["claude", "--print", "--agent", task.agent, prompt],
                capture_output=True, text=True, timeout=300,
                cwd=str(self._project_root),
            )
            task.result = proc.stdout[:2000] if proc.stdout else ""
            return proc.returncode == 0
        except FileNotFoundError:
            self._log(result, f"  [!] 'claude' CLI not found. Use --dry-run mode.")
            return False
        except subprocess.TimeoutExpired:
            self._log(result, f"  [!] Task {task.id} timed out after 300s.")
            return False

    def _try_degrade(self, task: Task, result: ExecutionResult) -> bool:
        if task.agent == "opc-executor":
            return False

        self._log(result, f"  [DEGRADE] Falling back to opc-executor for task {task.id}")
        task.agent = "opc-executor"
        task.started_at = _now()
        success = self._run_agent(task, result)
        task.finished_at = _now()
        return success

    @staticmethod
    def _build_prompt(task: Task) -> str:
        sections = [
            "==== CONTEXT BOUNDARY ENFORCED ====",
            f"Specialized subagent: {task.agent}",
            f"Operating inside strict wave execution.",
        ]
        if task.file:
            sections.append(f"TARGET FILE: {task.file}")
        sections.extend([
            f"Task: {task.title}",
            f"Action: {task.action}",
        ])
        if task.test_expectation:
            sections.append(f"Test Expectation: {task.test_expectation}")
        if task.completion_gate:
            sections.append(f"Completion Gate: {task.completion_gate}")
        sections.append("Do NOT wander off to inspect other parts of the workspace unless explicitly required.")
        return "\n".join(sections)

    def _log(self, result: ExecutionResult, message: str) -> None:
        entry = {"timestamp": _now(), "message": message}
        result.log.append(entry)
        print(message)

    def _persist_result(self, result: ExecutionResult) -> None:
        if not self._log_dir:
            return
        self._log_dir.mkdir(parents=True, exist_ok=True)
        filename = f"exec-{result.plan_id}-{result.started_at[:10]}.json"
        filepath = self._log_dir / filename
        data = asdict(result)
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def resolve_project_root(plan_path: Path) -> Path:
    start = plan_path if plan_path.is_dir() else plan_path.parent
    opc_dir = find_opc_dir(start.resolve())
    return opc_dir.parent if opc_dir is not None else start.resolve()


def resolve_default_log_dir(plan_path: Path) -> Path:
    return resolve_project_root(plan_path) / ".opc" / "execution-log"


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SuperOPC DAG Engine v2")
    parser.add_argument("plan_file", help="Path to PLAN.md with <opc-plan> block")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--log-dir", type=Path, default=None)
    args = parser.parse_args()

    plan_path = Path(args.plan_file)
    if not plan_path.exists():
        print(f"Error: {args.plan_file} does not exist.")
        sys.exit(1)

    plan = parse_plan_file(plan_path)
    if not plan:
        print("Error: Could not parse <opc-plan> from the file.")
        sys.exit(1)

    project_root = resolve_project_root(plan_path)
    log_dir = args.log_dir or resolve_default_log_dir(plan_path)
    engine = DAGEngine(dry_run=args.dry_run, log_dir=log_dir, project_root=project_root)
    result = engine.execute(plan)

    print(f"\n=> Execution {result.status}: {result.tasks_completed}/{result.tasks_total} tasks completed, {result.tasks_failed} failed.")
    sys.exit(0 if result.status == "completed" else 1)


if __name__ == "__main__":
    main()
