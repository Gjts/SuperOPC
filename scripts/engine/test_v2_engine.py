#!/usr/bin/env python3
"""Comprehensive tests for all SuperOPC v2 engine modules."""

import json
import sys
import tempfile
from pathlib import Path

PASS = 0
FAIL = 0

def report(name: str, ok: bool, detail: str = ""):
    global PASS, FAIL
    if ok:
        PASS += 1
        print(f"  PASS: {name}")
    else:
        FAIL += 1
        print(f"  FAIL: {name} — {detail}")


# =========================================================================
# 1. EventBus
# =========================================================================
print("=" * 60)
print("TEST SUITE 1: EventBus")
print("=" * 60)

from event_bus import EventBus, Event, get_event_bus, reset_event_bus, CORE_EVENTS

reset_event_bus()
bus = EventBus()
received = []
bus.subscribe("test.hello", lambda e: received.append(e))
event = bus.publish("test.hello", {"msg": "world"})
report("basic pub/sub", len(received) == 1 and received[0].payload["msg"] == "world")

wildcard_received = []
bus.subscribe("*", lambda e: wildcard_received.append(e))
bus.publish("anything.here", {"x": 1})
report("wildcard subscriber", len(wildcard_received) == 1 and wildcard_received[0].topic == "anything.here")

report("event history", len(bus.history) == 2)
report("recent filter", len(bus.recent(1)) == 1)

with tempfile.TemporaryDirectory() as tmpdir:
    jbus = EventBus(journal_dir=Path(tmpdir))
    jbus.publish("journal.test", {"data": 42})
    files = list(Path(tmpdir).glob("events-*.jsonl"))
    content = files[0].read_text(encoding="utf-8") if files else ""
    report("journal persistence", len(files) == 1 and "journal.test" in content)

reset_event_bus()
b1 = get_event_bus()
b2 = get_event_bus()
report("singleton pattern", b1 is b2)

report(f"core events ({len(CORE_EVENTS)} defined)", len(CORE_EVENTS) >= 20)

ev = Event(topic="t", payload={"a": 1}, source="test")
d = ev.to_dict()
report("Event.to_dict()", d["topic"] == "t" and d["payload"]["a"] == 1)


# =========================================================================
# 2. StateEngine
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 2: StateEngine")
print("=" * 60)

from state_engine import StateEngine, ProjectState, ProjectPhase, VALID_TRANSITIONS

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    opc = Path(tmpdir)
    bus = EventBus()
    engine = StateEngine(opc, bus)
    state = engine.load()
    report("fresh state", state.status == ProjectPhase.IDLE and state.project_name == "Unnamed Project")

    engine.update(project_name="TestProject", current_focus="MVP")
    report("update fields", engine.state.project_name == "TestProject")

    ok = engine.transition(ProjectPhase.PLANNING, reason="start")
    report("valid transition IDLE->PLANNING", ok and engine.state.status == ProjectPhase.PLANNING)

    bad = engine.transition(ProjectPhase.SHIPPING, reason="skip")
    report("invalid transition blocked", not bad and engine.state.status == ProjectPhase.PLANNING)

    engine.save()
    j_exists = (opc / "state.json").exists()
    m_exists = (opc / "STATE.md").exists()
    report("dual-write files exist", j_exists and m_exists)

    if j_exists:
        data = json.loads((opc / "state.json").read_text(encoding="utf-8"))
        report("JSON content correct", data["project_name"] == "TestProject" and data["status"] == "planning")
    if m_exists:
        md = (opc / "STATE.md").read_text(encoding="utf-8")
        report("Markdown content correct", "TestProject" in md and "MVP" in md)

    engine2 = StateEngine(opc, bus)
    s2 = engine2.load()
    report("reload from JSON", s2.project_name == "TestProject" and s2.status == ProjectPhase.PLANNING)

    engine.add_blocker("API key missing")
    report("add blocker", len(engine.state.blockers) == 1)
    engine.resolve_blocker("API key missing")
    report("resolve blocker", len(engine.state.blockers) == 0)

    all_transitions_valid = all(
        isinstance(v, frozenset) for v in VALID_TRANSITIONS.values()
    )
    report("transition table complete", all_transitions_valid and len(VALID_TRANSITIONS) == 7)


# =========================================================================
# 3. DecisionEngine
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 3: DecisionEngine")
print("=" * 60)

from decision_engine import (
    DecisionEngine, RuleEngine, StateMachineEngine, HeuristicEngine,
    ActionZone, ActionType, Decision, ZONE_MAP,
)

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    opc = Path(tmpdir)
    bus = EventBus()
    se = StateEngine(opc, bus)
    se.load()
    de = DecisionEngine(se, bus)

    d = de.decide()
    report(f"idle -> {d.command}", d.action in (ActionType.PLAN, ActionType.HEALTH_CHECK, ActionType.COLLECT_INTEL))

    se.add_blocker("Payment down")
    d = de.decide()
    report("blocker -> /opc-discuss", d.action == ActionType.DISCUSS)

    se.resolve_blocker("Payment down")
    d = de.decide({"handoff_exists": True})
    report("handoff -> /opc-resume", d.action == ActionType.RESUME)

    d = de.decide({"quality_violations": ["SQL injection found"]})
    report("security -> RED zone", d.zone == ActionZone.RED and d.requires_approval)

    se.transition(ProjectPhase.EXECUTING, reason="test")
    d = de.decide()
    report("executing -> /opc-build", d.action == ActionType.BUILD)

    se.transition(ProjectPhase.REVIEWING, reason="test")
    d = de.decide()
    report("reviewing -> /opc-review", d.action == ActionType.REVIEW)

    h = de.recent_decisions(10)
    report(f"decision history ({len(h)} entries)", len(h) >= 4)

    report("zone map completeness", len(ZONE_MAP) >= 20)

    with tempfile.TemporaryDirectory() as tmpdir2:
        fp = Path(tmpdir2) / "decisions.json"
        de.persist_history(fp)
        report("persist history to file", fp.exists())


# =========================================================================
# 4. DAG Engine
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 4: DAG Engine v2")
print("=" * 60)

from dag_engine import (
    DAGEngine, ExecutionPlan, Wave, Task as DTask, AgentRegistry,
    parse_plan_file, ExecutionResult,
)

reset_event_bus()

registry = AgentRegistry(Path("nonexistent_registry.json"))
report("registry loads without file", len(registry.all_agents) == 0)

real_registry_path = Path(__file__).resolve().parent.parent.parent / "agents" / "registry.json"
if real_registry_path.exists():
    reg = AgentRegistry(real_registry_path)
    report(f"registry loads {len(reg.all_agents)} agents", len(reg.all_agents) >= 15)

    t_fe = DTask(id="1", title="Build login UI component", action="Create React form")
    agent = reg.route(t_fe)
    report(f"frontend task -> {agent}", "frontend" in agent.lower() or agent == "opc-executor")

    t_be = DTask(id="2", title="Create REST API endpoint for users", action="Implement CRUD")
    agent = reg.route(t_be)
    report(f"backend task -> {agent}", "backend" in agent.lower() or "architect" in agent.lower() or agent == "opc-executor")

    t_sec = DTask(id="3", title="Security audit on auth module", action="OWASP scan")
    agent = reg.route(t_sec)
    report(f"security task -> {agent}", "security" in agent.lower())

plan = ExecutionPlan(
    goal="Test goal",
    waves=[
        Wave(id="1", description="Wave 1", tasks=[
            DTask(id="t1", title="Task A", action="Do A"),
            DTask(id="t2", title="Task B", action="Do B"),
        ]),
        Wave(id="2", description="Wave 2", tasks=[
            DTask(id="t3", title="Task C", action="Do C", depends_on=["t1", "t2"]),
        ]),
    ],
)

with tempfile.TemporaryDirectory() as tmpdir:
    log_dir = Path(tmpdir) / "log"
    bus = EventBus()
    engine = DAGEngine(dry_run=True, log_dir=log_dir, bus=bus)
    result = engine.execute(plan)
    report("dry-run execution completes", result.status == "completed")
    report(f"tasks: {result.tasks_completed}/{result.tasks_total}", result.tasks_completed == 3)
    report("waves completed", result.waves_completed == 2)
    log_files = list(log_dir.glob("exec-*.json"))
    report("execution log persisted", len(log_files) == 1)

with tempfile.TemporaryDirectory() as tmpdir:
    plan_md = Path(tmpdir) / "PLAN.md"
    plan_md.write_text("""# Test Plan

<opc-plan>
<metadata><goal>Test parsing</goal></metadata>
<waves>
  <wave id="1" description="Init">
    <task id="t1"><title>Setup</title><file>main.py</file><action>Create file</action></task>
  </wave>
</waves>
</opc-plan>
""", encoding="utf-8")
    parsed = parse_plan_file(plan_md)
    report("parse PLAN.md", parsed is not None and parsed.goal == "Test parsing")
    report("parsed wave/task", len(parsed.waves) == 1 and len(parsed.waves[0].tasks) == 1)


# =========================================================================
# 5. ProfileEngine
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 5: ProfileEngine")
print("=" * 60)

from profile_engine import ProfileEngine, DeveloperProfile

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    pe = ProfileEngine(profile_dir=Path(tmpdir))
    p = pe.load()
    report("default profile", p.communication_style == "balanced" and p.interaction_count == 0)

    pe.record_interaction(command="/opc-plan", project="demo")
    report("record interaction", pe.profile.interaction_count == 1)
    report("command tracked", pe.profile.preferred_commands.get("/opc-plan") == 1)
    report("project tracked", "demo" in pe.profile.projects_seen)

    pe.record_interaction(signals={"tech_stack": "nextjs", "communication_style": "terse"})
    report("signals applied", pe.profile.communication_style == "terse")
    report("tech stack added", "nextjs" in pe.profile.tech_stack_affinity)

    ctx = pe.get_context_injection()
    report("context injection", "developer_profile" in ctx)

    pe2 = ProfileEngine(profile_dir=Path(tmpdir))
    p2 = pe2.load()
    report("profile persistence", p2.interaction_count == 2 and p2.communication_style == "terse")


# =========================================================================
# 6. LearningStore
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 6: LearningStore")
print("=" * 60)

from learning_store import LearningStore, LearningCategory

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    ls = LearningStore(store_dir=Path(tmpdir))
    l = ls.capture(
        category=LearningCategory.TECHNICAL,
        title="Next.js SSR gotcha",
        content="Always check hydration mismatch on dynamic routes.",
        tags=["nextjs", "ssr"],
        source_project="demo",
    )
    report("capture learning", l.id and l.category == "technical")

    results = ls.query(category="technical")
    report("query by category", len(results) == 1 and results[0].title == "Next.js SSR gotcha")

    results = ls.query(tags=["nextjs"])
    report("query by tags", len(results) == 1)

    results = ls.query(keyword="hydration")
    report("query by keyword", len(results) == 1)

    results = ls.query(keyword="nonexistent")
    report("query no match", len(results) == 0)

    ctx = ls.get_context_injection(tags=["nextjs"])
    report("context injection", len(ctx) == 1 and ctx[0]["title"] == "Next.js SSR gotcha")

    stats = ls.stats()
    report("stats", stats["total"] == 1 and stats["by_category"]["technical"] == 1)

    ls2 = LearningStore(store_dir=Path(tmpdir))
    r2 = ls2.query()
    report("persistence reload", len(r2) == 1)


# =========================================================================
# 7. Notification
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 7: Notification")
print("=" * 60)

from notification import NotificationDispatcher, Notification, FileChannel

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    opc = Path(tmpdir)
    nd = NotificationDispatcher(opc)
    n = nd.notify("Test Alert", "Something happened", level="info")
    report("notification created", n.delivered and n.title == "Test Alert")

    notif_dir = opc / "notifications"
    files = list(notif_dir.glob("*.json"))
    report("notification file written", len(files) == 1)

    content = json.loads(files[0].read_text(encoding="utf-8"))
    report("notification content", content["title"] == "Test Alert" and content["level"] == "info")

    recent = nd.recent(5)
    report("recent notifications", len(recent) == 1)

    report("unread count", nd.unread_count == 1)


# =========================================================================
# 8. CruiseController
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 8: CruiseController")
print("=" * 60)

from cruise_controller import CruiseController, CruiseMode
import time

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    opc = Path(tmpdir)
    cc = CruiseController(opc, mode=CruiseMode.WATCH, heartbeat_seconds=1)

    report("initial state", not cc.status.running and cc.status.mode == CruiseMode.WATCH)

    cc.start(hours=0.001)
    time.sleep(2.5)
    report("cruise ran heartbeats", cc.status.heartbeat_count >= 1)

    summary = cc.get_summary()
    report("summary has fields", "mode" in summary and "heartbeats" in summary)

    cc.stop(reason="test")
    report("cruise stopped", not cc.status.running)

    log_dir = opc / "cruise-log"
    status_file = log_dir / "status.json"
    report("status persisted", status_file.exists())


# =========================================================================
# 9. Scheduler
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 9: Scheduler")
print("=" * 60)

from scheduler import Scheduler

reset_event_bus()

counter = {"value": 0}
def increment():
    counter["value"] += 1

sched = Scheduler()
sched.add_job("test_job", interval_seconds=1, callback=increment)
sched.start()
time.sleep(2.5)
sched.stop()
report(f"scheduler ran job {counter['value']} times", counter["value"] >= 1)

jobs = sched.jobs
report("job listing", "test_job" in jobs and jobs["test_job"]["run_count"] >= 1)


# =========================================================================
# 10. ContextAssembler
# =========================================================================
print("\n" + "=" * 60)
print("TEST SUITE 10: ContextAssembler")
print("=" * 60)

from context_assembler import ContextAssembler, BUDGET_PROFILES, PHASE_SKILL_PRIORITY

reset_event_bus()

with tempfile.TemporaryDirectory() as tmpdir:
    opc = Path(tmpdir)
    bus = EventBus()
    se = StateEngine(opc, bus)
    se.load()
    se.update(project_name="AssemblerTest", current_focus="MVP auth")

    pe = ProfileEngine(profile_dir=Path(tmpdir) / "profile")
    ls = LearningStore(store_dir=Path(tmpdir) / "learn")

    assembler = ContextAssembler(
        repo_root=Path(__file__).resolve().parent.parent.parent,
        state_engine=se,
        profile_engine=pe,
        learning_store=ls,
    )

    ctx = assembler.assemble()
    report("assemble returns dict", isinstance(ctx, dict))
    report("has skills", "skills" in ctx and len(ctx["skills"]) > 0)
    report("has agents", "agents" in ctx and len(ctx["agents"]) > 0)
    report("has behavior protocol", "behavior_protocol" in ctx and len(ctx["behavior_protocol"]) >= 4)
    report("has developer profile", "developer_profile" in ctx)

    se.transition(ProjectPhase.EXECUTING, reason="test")
    ctx2 = assembler.assemble(task_hint="tdd testing")
    report("executing phase skills include tdd", "tdd" in ctx2["skills"])

    md = assembler.generate_dynamic_claude_md()
    report("dynamic CLAUDE.md generated", "Behavior Protocol" in md and "AssemblerTest" in md)
    report("dynamic CLAUDE.md has skills", "Active Skills" in md)

    report("budget profiles defined", len(BUDGET_PROFILES) == 4)
    report("phase-skill map complete", len(PHASE_SKILL_PRIORITY) == 7)


# =========================================================================
# Summary
# =========================================================================
print("\n" + "=" * 60)
total = PASS + FAIL
print(f"RESULTS: {PASS}/{total} passed, {FAIL} failed")
if FAIL == 0:
    print("ALL TESTS PASSED!")
else:
    print(f"THERE WERE {FAIL} FAILURES")
print("=" * 60)
sys.exit(1 if FAIL else 0)
