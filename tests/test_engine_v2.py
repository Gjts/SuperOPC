"""Pytest-compatible tests for SuperOPC v2 engine modules.

Converted from scripts/engine/test_v2_engine.py (manual script)
into pytest-native functions with proper fixtures and assertions.
"""

from __future__ import annotations

import json
import time
from pathlib import Path

import pytest

from event_bus import CORE_EVENTS, Event, EventBus, get_event_bus, reset_event_bus
from state_engine import (
    VALID_TRANSITIONS,
    ProjectPhase,
    ProjectState,
    StateEngine,
)
from decision_engine import (
    ActionType,
    ActionZone,
    Decision,
    DecisionEngine,
    HeuristicEngine,
    RuleEngine,
    StateMachineEngine,
)
from dag_engine import (
    AgentRegistry,
    DAGEngine,
    ExecutionPlan,
    ExecutionResult,
    Wave,
    parse_plan_file,
)
from dag_engine import Task as DTask
from profile_engine import DeveloperProfile, ProfileEngine
from learning_store import LearningCategory, LearningStore
from notification import FileChannel, Notification, NotificationDispatcher
from cruise_controller import CruiseController, CruiseMode
from scheduler import Scheduler
from context_assembler import BUDGET_PROFILES, PHASE_SKILL_PRIORITY, ContextAssembler

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _reset_bus():
    reset_event_bus()
    yield
    reset_event_bus()


# =========================================================================
# EventBus
# =========================================================================

class TestEventBus:
    def test_basic_pub_sub(self):
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("test.hello", lambda e: received.append(e))
        bus.publish("test.hello", {"msg": "world"})
        assert len(received) == 1
        assert received[0].payload["msg"] == "world"

    def test_wildcard_subscriber(self):
        bus = EventBus()
        received: list[Event] = []
        bus.subscribe("*", lambda e: received.append(e))
        bus.publish("anything.here", {"x": 1})
        assert len(received) == 1
        assert received[0].topic == "anything.here"

    def test_event_history(self):
        bus = EventBus()
        bus.publish("a", {})
        bus.publish("b", {})
        assert len(bus.history) == 2

    def test_recent_filter(self):
        bus = EventBus()
        bus.publish("a", {})
        bus.publish("b", {})
        assert len(bus.recent(1)) == 1

    def test_journal_persistence(self, tmp_path: Path):
        bus = EventBus(journal_dir=tmp_path)
        bus.publish("journal.test", {"data": 42})
        files = list(tmp_path.glob("events-*.jsonl"))
        assert len(files) == 1
        content = files[0].read_text(encoding="utf-8")
        assert "journal.test" in content

    def test_singleton_pattern(self):
        b1 = get_event_bus()
        b2 = get_event_bus()
        assert b1 is b2

    def test_core_events_defined(self):
        assert len(CORE_EVENTS) >= 20

    def test_event_to_dict(self):
        ev = Event(topic="t", payload={"a": 1}, source="test")
        d = ev.to_dict()
        assert d["topic"] == "t"
        assert d["payload"]["a"] == 1


# =========================================================================
# StateEngine
# =========================================================================

class TestStateEngine:
    def test_fresh_state(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        state = engine.load()
        assert state.status == ProjectPhase.IDLE
        assert state.project_name == "Unnamed Project"

    def test_update_fields(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        engine.update(project_name="TestProject", current_focus="MVP")
        assert engine.state.project_name == "TestProject"

    def test_valid_transition(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        ok = engine.transition(ProjectPhase.PLANNING, reason="start")
        assert ok
        assert engine.state.status == ProjectPhase.PLANNING

    def test_invalid_transition_blocked(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        bad = engine.transition(ProjectPhase.SHIPPING, reason="skip")
        assert not bad
        assert engine.state.status == ProjectPhase.IDLE

    def test_dual_write_files_exist(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        engine.update(project_name="TestProject", current_focus="MVP")
        engine.save()
        assert (tmp_path / "state.json").exists()
        assert (tmp_path / "STATE.md").exists()

    def test_json_content_correct(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        engine.update(project_name="TestProject")
        engine.transition(ProjectPhase.PLANNING, reason="test")
        data = json.loads((tmp_path / "state.json").read_text(encoding="utf-8"))
        assert data["project_name"] == "TestProject"
        assert data["status"] == "planning"

    def test_markdown_content_correct(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        engine.update(project_name="TestProject", current_focus="MVP")
        md = (tmp_path / "STATE.md").read_text(encoding="utf-8")
        assert "TestProject" in md
        assert "MVP" in md

    def test_reload_from_json(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        engine.update(project_name="TestProject")
        engine.transition(ProjectPhase.PLANNING, reason="test")

        engine2 = StateEngine(tmp_path, bus)
        s2 = engine2.load()
        assert s2.project_name == "TestProject"
        assert s2.status == ProjectPhase.PLANNING

    def test_add_and_resolve_blocker(self, tmp_path: Path):
        bus = EventBus()
        engine = StateEngine(tmp_path, bus)
        engine.load()
        engine.add_blocker("API key missing")
        assert len(engine.state.blockers) == 1
        engine.resolve_blocker("API key missing")
        assert len(engine.state.blockers) == 0

    def test_transition_table_complete(self):
        assert all(isinstance(v, frozenset) for v in VALID_TRANSITIONS.values())
        assert len(VALID_TRANSITIONS) == 7


# =========================================================================
# DecisionEngine
# =========================================================================

class TestDecisionEngine:
    def test_idle_decision(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        d = de.decide()
        assert d.action in (ActionType.PLAN, ActionType.HEALTH_CHECK, ActionType.COLLECT_INTEL)

    def test_blocker_triggers_discuss(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        se.add_blocker("Payment down")
        d = de.decide()
        assert d.action == ActionType.DISCUSS

    def test_handoff_triggers_resume(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        se.resolve_blocker("Payment down") if "Payment down" in se.state.blockers else None
        d = de.decide({"handoff_exists": True})
        assert d.action == ActionType.RESUME

    def test_security_violation_red_zone(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        d = de.decide({"quality_violations": ["SQL injection found"]})
        assert d.zone == ActionZone.RED
        assert d.requires_approval

    def test_executing_phase_builds(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        se.transition(ProjectPhase.EXECUTING, reason="test")
        d = de.decide()
        assert d.action == ActionType.BUILD

    def test_reviewing_phase_reviews(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        se.transition(ProjectPhase.EXECUTING, reason="step1")
        se.transition(ProjectPhase.REVIEWING, reason="step2")
        d = de.decide()
        assert d.action == ActionType.REVIEW

    def test_decision_history(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        de = DecisionEngine(se, bus)
        de.decide()
        de.decide()
        assert len(de.recent_decisions(10)) >= 2


# =========================================================================
# DAG Engine
# =========================================================================

class TestDAGEngine:
    def test_empty_registry_loads(self):
        registry = AgentRegistry(Path("nonexistent_registry.json"))
        assert len(registry.all_agents) == 0

    def test_real_registry_loads(self):
        real_path = REPO_ROOT / "agents" / "registry.json"
        if not real_path.exists():
            pytest.skip("registry.json not found")
        reg = AgentRegistry(real_path)
        assert len(reg.all_agents) >= 15

    def test_frontend_task_routing(self):
        real_path = REPO_ROOT / "agents" / "registry.json"
        if not real_path.exists():
            pytest.skip("registry.json not found")
        reg = AgentRegistry(real_path)
        task = DTask(id="1", title="Build login UI component", action="Create React form")
        agent = reg.route(task)
        assert "frontend" in agent.lower() or agent == "opc-executor"

    def test_backend_task_routing(self):
        real_path = REPO_ROOT / "agents" / "registry.json"
        if not real_path.exists():
            pytest.skip("registry.json not found")
        reg = AgentRegistry(real_path)
        task = DTask(id="2", title="Create REST API endpoint for users", action="Implement CRUD")
        agent = reg.route(task)
        assert "backend" in agent.lower() or "architect" in agent.lower() or agent == "opc-executor"

    def test_security_task_routing(self):
        real_path = REPO_ROOT / "agents" / "registry.json"
        if not real_path.exists():
            pytest.skip("registry.json not found")
        reg = AgentRegistry(real_path)
        task = DTask(id="3", title="Security audit on auth module", action="OWASP scan")
        agent = reg.route(task)
        assert "security" in agent.lower()

    def test_intel_task_routing(self):
        real_path = REPO_ROOT / "agents" / "registry.json"
        if not real_path.exists():
            pytest.skip("registry.json not found")
        reg = AgentRegistry(real_path)
        task = DTask(id="4", title="Refresh codebase intelligence index", action="Rebuild stack and dependency-graph intel")
        agent = reg.route(task)
        assert agent == "opc-intel-updater" or "intel" in agent.lower()

    def test_dry_run_execution(self, tmp_path: Path):
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
        log_dir = tmp_path / "log"
        bus = EventBus()
        engine = DAGEngine(dry_run=True, log_dir=log_dir, bus=bus)
        result = engine.execute(plan)
        assert result.status == "completed"
        assert result.tasks_completed == 3
        assert result.waves_completed == 2
        assert list(log_dir.glob("exec-*.json"))

    def test_parse_plan_file(self, tmp_path: Path):
        plan_md = tmp_path / "PLAN.md"
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
        assert parsed is not None
        assert parsed.goal == "Test parsing"
        assert len(parsed.waves) == 1
        assert len(parsed.waves[0].tasks) == 1


# =========================================================================
# ProfileEngine
# =========================================================================

class TestProfileEngine:
    def test_default_profile(self, tmp_path: Path):
        pe = ProfileEngine(profile_dir=tmp_path)
        p = pe.load()
        assert p.communication_style == "balanced"
        assert p.interaction_count == 0

    def test_record_interaction(self, tmp_path: Path):
        pe = ProfileEngine(profile_dir=tmp_path)
        pe.load()
        pe.record_interaction(command="/opc-plan", project="demo")
        assert pe.profile.interaction_count == 1
        assert pe.profile.preferred_commands.get("/opc-plan") == 1
        assert "demo" in pe.profile.projects_seen

    def test_signals_applied(self, tmp_path: Path):
        pe = ProfileEngine(profile_dir=tmp_path)
        pe.load()
        pe.record_interaction(signals={"tech_stack": "nextjs", "communication_style": "terse"})
        assert pe.profile.communication_style == "terse"
        assert "nextjs" in pe.profile.tech_stack_affinity

    def test_context_injection(self, tmp_path: Path):
        pe = ProfileEngine(profile_dir=tmp_path)
        pe.load()
        ctx = pe.get_context_injection()
        assert "developer_profile" in ctx

    def test_profile_persistence(self, tmp_path: Path):
        pe = ProfileEngine(profile_dir=tmp_path)
        pe.load()
        pe.record_interaction(command="/opc-plan")
        pe.record_interaction(signals={"communication_style": "terse"})

        pe2 = ProfileEngine(profile_dir=tmp_path)
        p2 = pe2.load()
        assert p2.interaction_count == 2
        assert p2.communication_style == "terse"


# =========================================================================
# LearningStore
# =========================================================================

class TestLearningStore:
    def test_capture_learning(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        entry = ls.capture(
            category=LearningCategory.TECHNICAL,
            title="Next.js SSR gotcha",
            content="Always check hydration mismatch on dynamic routes.",
            tags=["nextjs", "ssr"],
            source_project="demo",
        )
        assert entry.id
        assert entry.category == "technical"

    def test_query_by_category(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        ls.capture(category=LearningCategory.TECHNICAL, title="Test", content="c", tags=[], source_project="p")
        results = ls.query(category="technical")
        assert len(results) == 1

    def test_query_by_tags(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        ls.capture(category=LearningCategory.TECHNICAL, title="T", content="c", tags=["nextjs"], source_project="p")
        assert len(ls.query(tags=["nextjs"])) == 1

    def test_query_by_keyword(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        ls.capture(category=LearningCategory.TECHNICAL, title="T", content="hydration issue", tags=[], source_project="p")
        assert len(ls.query(keyword="hydration")) == 1
        assert len(ls.query(keyword="nonexistent")) == 0

    def test_context_injection(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        ls.capture(category=LearningCategory.TECHNICAL, title="Tip", content="c", tags=["react"], source_project="p")
        ctx = ls.get_context_injection(tags=["react"])
        assert len(ctx) == 1

    def test_stats(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        ls.capture(category=LearningCategory.TECHNICAL, title="T", content="c", tags=[], source_project="p")
        stats = ls.stats()
        assert stats["total"] == 1
        assert stats["by_category"]["technical"] == 1

    def test_persistence_reload(self, tmp_path: Path):
        ls = LearningStore(store_dir=tmp_path)
        ls.capture(category=LearningCategory.TECHNICAL, title="T", content="c", tags=[], source_project="p")
        ls2 = LearningStore(store_dir=tmp_path)
        assert len(ls2.query()) == 1


# =========================================================================
# Notification
# =========================================================================

class TestNotification:
    def test_notification_created(self, tmp_path: Path):
        nd = NotificationDispatcher(tmp_path)
        n = nd.notify("Test Alert", "Something happened", level="info")
        assert n.delivered
        assert n.title == "Test Alert"

    def test_notification_file_written(self, tmp_path: Path):
        nd = NotificationDispatcher(tmp_path)
        nd.notify("Test Alert", "Something happened", level="info")
        files = list((tmp_path / "notifications").glob("*.json"))
        assert len(files) == 1
        content = json.loads(files[0].read_text(encoding="utf-8"))
        assert content["title"] == "Test Alert"
        assert content["level"] == "info"

    def test_recent_and_unread(self, tmp_path: Path):
        nd = NotificationDispatcher(tmp_path)
        nd.notify("Alert", "body", level="info")
        assert len(nd.recent(5)) == 1
        assert nd.unread_count == 1


# =========================================================================
# CruiseController
# =========================================================================

class TestCruiseController:
    def test_initial_state(self, tmp_path: Path):
        cc = CruiseController(tmp_path, mode=CruiseMode.WATCH, heartbeat_seconds=1)
        assert not cc.status.running
        assert cc.status.mode == CruiseMode.WATCH

    def test_cruise_runs_heartbeats(self, tmp_path: Path):
        cc = CruiseController(tmp_path, mode=CruiseMode.WATCH, heartbeat_seconds=1)
        cc.start(hours=0.001)
        time.sleep(2.5)
        assert cc.status.heartbeat_count >= 1
        cc.stop(reason="test")

    def test_summary_fields(self, tmp_path: Path):
        cc = CruiseController(tmp_path, mode=CruiseMode.WATCH, heartbeat_seconds=1)
        summary = cc.get_summary()
        assert "mode" in summary
        assert "heartbeats" in summary

    def test_stop_persists_status(self, tmp_path: Path):
        cc = CruiseController(tmp_path, mode=CruiseMode.WATCH, heartbeat_seconds=1)
        cc.start(hours=0.001)
        time.sleep(1.5)
        cc.stop(reason="test")
        assert not cc.status.running
        assert (tmp_path / "cruise-log" / "status.json").exists()


# =========================================================================
# Scheduler
# =========================================================================

class TestScheduler:
    def test_scheduler_runs_job(self):
        counter = {"value": 0}
        def increment():
            counter["value"] += 1

        sched = Scheduler()
        sched.add_job("test_job", interval_seconds=1, callback=increment)
        sched.start()
        time.sleep(2.5)
        sched.stop()
        assert counter["value"] >= 1

    def test_job_listing(self):
        sched = Scheduler()
        sched.add_job("test_job", interval_seconds=1, callback=lambda: None)
        sched.start()
        time.sleep(1.5)
        sched.stop()
        jobs = sched.jobs
        assert "test_job" in jobs


# =========================================================================
# ContextAssembler
# =========================================================================

class TestContextAssembler:
    def test_assemble_returns_dict(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        se.update(project_name="AssemblerTest", current_focus="MVP auth")
        pe = ProfileEngine(profile_dir=tmp_path / "profile")
        ls = LearningStore(store_dir=tmp_path / "learn")
        assembler = ContextAssembler(
            repo_root=REPO_ROOT,
            state_engine=se,
            profile_engine=pe,
            learning_store=ls,
        )
        ctx = assembler.assemble()
        assert isinstance(ctx, dict)
        assert "skills" in ctx and len(ctx["skills"]) > 0
        assert "agents" in ctx and len(ctx["agents"]) > 0
        assert "behavior_protocol" in ctx and len(ctx["behavior_protocol"]) >= 4
        assert "developer_profile" in ctx

    def test_executing_phase_includes_tdd(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        se.update(project_name="AssemblerTest")
        se.transition(ProjectPhase.EXECUTING, reason="test")
        pe = ProfileEngine(profile_dir=tmp_path / "profile")
        ls = LearningStore(store_dir=tmp_path / "learn")
        assembler = ContextAssembler(
            repo_root=REPO_ROOT,
            state_engine=se,
            profile_engine=pe,
            learning_store=ls,
        )
        ctx = assembler.assemble(task_hint="tdd testing")
        assert "tdd" in ctx["skills"]

    def test_dynamic_claude_md(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        se.update(project_name="AssemblerTest")
        pe = ProfileEngine(profile_dir=tmp_path / "profile")
        ls = LearningStore(store_dir=tmp_path / "learn")
        assembler = ContextAssembler(
            repo_root=REPO_ROOT,
            state_engine=se,
            profile_engine=pe,
            learning_store=ls,
        )
        md = assembler.generate_dynamic_claude_md()
        assert "Behavior Protocol" in md
        assert "AssemblerTest" in md
        assert "Active Skills" in md

    def test_budget_profiles_and_phase_map(self):
        assert len(BUDGET_PROFILES) == 4
        assert len(PHASE_SKILL_PRIORITY) == 7

    def test_personal_rules_loaded_when_present(self, tmp_path: Path):
        bus = EventBus()
        se = StateEngine(tmp_path, bus)
        se.load()
        se.transition(ProjectPhase.EXECUTING)
        repo_fake = tmp_path / "repo"
        personal = repo_fake / "rules" / "personal"
        personal.mkdir(parents=True)
        (personal / "workflow.md").write_text("# auto rule", encoding="utf-8")
        assembler = ContextAssembler(
            repo_root=repo_fake,
            state_engine=se,
            profile_engine=ProfileEngine(profile_dir=tmp_path / "p"),
            learning_store=LearningStore(store_dir=tmp_path / "l"),
        )
        ctx = assembler.assemble()
        assert any("personal/" in r for r in ctx["rules"])


# ========================================================================== #
# InstinctGenerator
# ========================================================================== #

class TestInstinctGenerator:
    def test_no_patterns_returns_empty(self, tmp_path: Path):
        from instinct_generator import InstinctGenerator
        store = LearningStore(store_dir=tmp_path / "learn", bus=EventBus())
        gen = InstinctGenerator(repo_root=tmp_path, store=store, bus=EventBus())
        result = gen.run(min_occurrences=3)
        assert result == []

    def test_generates_instincts_from_observations(self, tmp_path: Path):
        from instinct_generator import InstinctGenerator
        store = LearningStore(store_dir=tmp_path / "learn", bus=EventBus())
        obs_file = tmp_path / "learn" / "observations.jsonl"
        obs_file.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for i in range(20):
            lines.append(json.dumps({"ts": "2026-04-01T10:00:00Z", "tool": "Bash", "action": "shell", "context": f"cmd-{i}", "project": "test"}))
        obs_file.write_text("\n".join(lines), encoding="utf-8")

        gen = InstinctGenerator(repo_root=tmp_path, store=store, bus=EventBus())
        result = gen.run(min_occurrences=5)
        assert len(result) > 0
        rules_dir = tmp_path / "rules" / "personal"
        assert rules_dir.is_dir()
        assert any(rules_dir.glob("*.md"))
        assert (rules_dir / "instinct-index.json").exists()

    def test_dry_run_writes_no_files(self, tmp_path: Path):
        from instinct_generator import InstinctGenerator
        store = LearningStore(store_dir=tmp_path / "learn", bus=EventBus())
        obs_file = tmp_path / "learn" / "observations.jsonl"
        obs_file.parent.mkdir(parents=True, exist_ok=True)
        lines = [json.dumps({"ts": "2026-04-01T10:00:00Z", "tool": "Grep", "action": "search", "context": "", "project": "t"}) for _ in range(20)]
        obs_file.write_text("\n".join(lines), encoding="utf-8")

        gen = InstinctGenerator(repo_root=tmp_path, store=store, bus=EventBus())
        result = gen.run(min_occurrences=5, dry_run=True)
        assert len(result) > 0
        assert not (tmp_path / "rules" / "personal").exists()

    def test_tdd_ratio_detection(self, tmp_path: Path):
        from instinct_generator import InstinctGenerator
        store = LearningStore(store_dir=tmp_path / "learn", bus=EventBus())
        obs_file = tmp_path / "learn" / "observations.jsonl"
        obs_file.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        for _ in range(15):
            lines.append(json.dumps({"ts": "2026-04-01T10:00:00Z", "tool": "Edit", "action": "edit-test", "context": "", "project": "t"}))
        for _ in range(10):
            lines.append(json.dumps({"ts": "2026-04-01T10:00:00Z", "tool": "Edit", "action": "edit-code", "context": "", "project": "t"}))
        obs_file.write_text("\n".join(lines), encoding="utf-8")

        gen = InstinctGenerator(repo_root=tmp_path, store=store, bus=EventBus())
        result = gen.run(min_occurrences=5)
        ids = [i.id for i in result]
        assert "testing-tdd-ratio" in ids


# ========================================================================== #
# MethodologyDatabase
# ========================================================================== #

class TestMethodologyDatabase:
    def test_builtin_methodologies_loaded(self):
        import sys
        sys.path.insert(0, str(REPO_ROOT / "scripts" / "intelligence"))
        from methodology_database import MethodologyDatabase
        db = MethodologyDatabase()
        domains = db.list_domains()
        assert len(domains) >= 5
        assert "validation" in domains
        assert "engineering" in domains

    def test_query_by_domain(self):
        from methodology_database import MethodologyDatabase
        db = MethodologyDatabase()
        results = db.query(domain="validation")
        assert len(results) >= 2
        names = [m.name for m in results]
        assert "The Mom Test" in names

    def test_query_by_keyword(self):
        from methodology_database import MethodologyDatabase
        db = MethodologyDatabase()
        results = db.query(keyword="pyramid")
        assert len(results) >= 1
        assert results[0].id == "minto-pyramid"

    def test_get_by_id(self):
        from methodology_database import MethodologyDatabase
        db = MethodologyDatabase()
        m = db.get("tdd-kent-beck")
        assert m is not None
        assert m.author == "Kent Beck"
        assert len(m.steps) >= 4

    def test_context_injection(self):
        from methodology_database import MethodologyDatabase
        db = MethodologyDatabase()
        injection = db.get_context_injection(domain="growth", limit=2)
        assert len(injection) >= 1
        assert "name" in injection[0]
        assert "one_liner" in injection[0]

    def test_add_custom_methodology(self, tmp_path: Path):
        from methodology_database import Methodology, MethodologyDatabase
        db = MethodologyDatabase(db_dir=tmp_path / "methods")
        custom = Methodology(
            id="custom-test",
            name="Test Method",
            author="Test Author",
            domain="testing",
            one_liner="A test methodology",
            core_principles=["principle 1"],
            steps=["step 1"],
            when_to_use=["testing"],
            common_mistakes=["mistake 1"],
        )
        db.add(custom)
        assert (tmp_path / "methods" / "custom-test.json").exists()
        retrieved = db.get("custom-test")
        assert retrieved is not None
        assert retrieved.name == "Test Method"
