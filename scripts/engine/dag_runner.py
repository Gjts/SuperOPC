#!/usr/bin/env python3
"""
dag_runner.py — DEPRECATED: Use dag_engine.py instead.

This is the v1 wave dispatcher retained for backward compatibility only.
All new code should import from dag_engine (v2) which provides:
  - Semantic agent routing via registry.json
  - Resilient execution with retry/degrade/escalate
  - Event bus integration
  - Execution history persistence

See dag_engine.py for the replacement.
"""

from __future__ import annotations

import argparse
import concurrent.futures
import re
import subprocess
import sys
if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PLANS_DIR = REPO_ROOT / "docs" / "plans"


class Task:
    def __init__(self, id: str, depends_on: List[str], title: str, file: str, action: str, test_exp: str, gate: str):
        self.id = id
        self.depends_on = depends_on
        self.title = title
        self.file = file
        self.action = action
        self.test_exp = test_exp
        self.gate = gate

    def __repr__(self) -> str:
        return f"<Task {self.id}: {self.title}>"


class Wave:
    def __init__(self, id: str, description: str, tasks: List[Task]):
        self.id = id
        self.description = description
        self.tasks = tasks

    def __repr__(self) -> str:
        return f"<Wave {self.id} ({len(self.tasks)} tasks)>"


class OpcPlan:
    def __init__(self, goal: str, waves: List[Wave]):
        self.goal = goal
        self.waves = waves


def parse_plan_file(file_path: Path) -> OpcPlan | None:
    content = file_path.read_text(encoding="utf-8")
    # Extract <opc-plan> block
    match = re.search(r"<opc-plan>([\s\S]*?)</opc-plan>", content)
    if not match:
        return None
    xml_content = "<opc-plan>" + match.group(1) + "</opc-plan>"
    try:
        root = ET.fromstring(xml_content)
    except ET.ParseError as e:
        print(f"[!] XML Parsing error: {e}")
        return None

    goal_node = root.find(".//metadata/goal")
    goal = goal_node.text.strip() if goal_node is not None and goal_node.text else "Unknown Goal"

    waves = []
    for wave_node in root.findall(".//waves/wave"):
        wave_id = wave_node.get("id", "0")
        desc = wave_node.get("description", "")
        tasks = []
        for task_node in wave_node.findall("task"):
            t_id = task_node.get("id", "")
            deps_str = task_node.get("depends_on", "")
            deps = [d.strip() for d in deps_str.split(",")] if deps_str else []
            
            t_title = getattr(task_node.find("title"), "text", "Untitled")
            t_file = getattr(task_node.find("file"), "text", "")
            t_action = getattr(task_node.find("action"), "text", "")
            t_test = getattr(task_node.find("test-expectation"), "text", "")
            t_gate = getattr(task_node.find("completion-gate"), "text", "")
            
            tasks.append(Task(t_id, deps, str(t_title).strip(), str(t_file).strip(), str(t_action).strip(), str(t_test).strip(), str(t_gate).strip()))
        waves.append(Wave(wave_id, desc, tasks))
    
    return OpcPlan(goal, waves)


def execute_subagent_task(task: Task, dry_run: bool = False) -> bool:
    # 动态矩阵路由判定 (Agency-Agents Matrixing)
    content_sig = f"{task.title.lower()} {task.action.lower()}"
    target_agent = "opc-executor"
    if any(k in content_sig for k in ["ui", "css", "frontend", "前端", "样式", "组件", "视口"]):
        target_agent = "opc-frontend-wizard"
    elif any(k in content_sig for k in ["api", "db", "数据库", "后端", "backend", "模型"]):
        target_agent = "opc-backend-architect"
    elif any(k in content_sig for k in ["audit", "scan", "安全", "security", "越权", "检查"]):
        target_agent = "opc-security-auditor"

    print(f"    [Executor] Specialized Routing: {target_agent} -> Task {task.id}: {task.title}")
    
    # 构建收束的上下文投射边界 (Context Projection)
    prompt = (
        f"==== CONTEXT BOUNDARY ENFORCED ====\n"
        f"You are the specialized subagent: {target_agent}.\n"
        f"You are operating inside a strict physical execution wave.\n"
        f"WARNING: Your view has been context-projected. You must ONLY read/write the following file:\n"
        f"--> [TARGET FILE]: {task.file} <--\n\n"
        f"Task Description: {task.title}\n"
        f"Action Required: {task.action}\n"
        f"Test Expectation: {task.test_exp}\n"
        f"Completion Gate: {task.gate}\n\n"
        f"Do NOT wander off to inspect other parts of the workspace unless explicitly required to import them."
    )
    
    if dry_run:
        print(f"    [Dry-Run] Spawned Agent: {target_agent} | Targeted File: {task.file}")
        import time
        time.sleep(1) # simulate work
        print(f"    [Executor] Finished Task {task.id} successfully.")
        return True

    # Real Subprocess Execution using claude-code CLI
    try:
        proc = subprocess.run(
            ["claude", "--print", "--agent", target_agent, prompt],
            capture_output=True,
            text=True,
        )
        if proc.returncode == 0:
            print(f"    [Executor] Finished Task {task.id} successfully.")
            return True
        else:
            print(f"    [!] Task {task.id} failed with exit code: {proc.returncode}")
            print(f"        Output: {proc.stderr}")
            return False
    except FileNotFoundError:
        print(f"    [!] 'claude' CLI not installed in path. Cannot spawn physical agent. (Dry run mode recommended)")
        return False


def run_dag(plan: OpcPlan, dry_run: bool = False):
    print(f"\n=> [DAG Runner] Target Goal: {plan.goal}")
    print(f"=> [DAG Runner] Total Waves: {len(plan.waves)}")
    
    for wave in plan.waves:
        print(f"\n==============================================")
        print(f"🌊 Executing Wave {wave.id}: {wave.description}")
        print(f"    Total concurrent tasks: {len(wave.tasks)}")
        
        # Parallel execution using ThreadPool
        with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(wave.tasks), 4)) as executor:
            future_to_task = {executor.submit(execute_subagent_task, task, dry_run): task for task in wave.tasks}
            
            for future in concurrent.futures.as_completed(future_to_task):
                task = future_to_task[future]
                try:
                    success = future.result()
                    if not success:
                        print(f"\n[FATAL] Wave {wave.id} failed at task {task.id}.")
                        print("[FATAL] Physical barrier triggered. Downstream waves aborted to prevent context rot.")
                        sys.exit(1)
                except Exception as exc:
                    print(f"\n[FATAL] Task {task.id} generated an exception: {exc}")
                    sys.exit(1)
                    
        print(f"✅ Wave {wave.id} cleared. Proceeding to next wave or finish.")

    print("\n=> [DAG Runner] All waves completed. Initiating Global Quality Gate...")
    try:
        q_proc = subprocess.run([sys.executable, str(REPO_ROOT / "scripts" / "opc_quality.py")], capture_output=True, text=True)
        if q_proc.returncode == 0:
            print("✅ [Quality Gate] Passed successfully.")
        else:
            print("⚠️ [Quality Gate] Issues found after wave execution:")
            print(q_proc.stdout or q_proc.stderr)
    except FileNotFoundError:
        print("⚠️ [Quality Gate] opc_quality.py script not found or could not execute.")


def main():
    parser = argparse.ArgumentParser(description="DAG Wave Runner for SuperOPC")
    parser.add_argument("plan_file", help="Path to the PLAN.md file containing the <opc-plan> block")
    parser.add_argument("--dry-run", action="store_true", help="Simulate execution without spawning real claude subagents")
    args = parser.parse_args()

    plan_path = Path(args.plan_file)
    if not plan_path.exists():
        print(f"Error: {args.plan_file} does not exist.")
        sys.exit(1)

    plan = parse_plan_file(plan_path)
    if not plan:
        print("Error: Could not parse <opc-plan> from the file.")
        sys.exit(1)

    run_dag(plan, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
