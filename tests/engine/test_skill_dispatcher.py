from __future__ import annotations

import json
import subprocess
import uuid
from pathlib import Path

import pytest

from engine.skill_dispatcher import dispatch_to_agent, resolve_dispatch_target

REPO_ROOT = Path(__file__).resolve().parents[2]


def _scratch_path(name: str) -> Path:
    root = REPO_ROOT / ".test_tmp" / "dispatch-engine-tests" / f"{name}-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def test_resolve_dispatch_target_rejects_atomic_skill() -> None:
    with pytest.raises(ValueError, match="not a dispatcher skill"):
        resolve_dispatch_target(skill_id="tdd")


def test_resolve_dispatch_target_rejects_intel_local_runtime_subcommand() -> None:
    with pytest.raises(ValueError, match="local runtime"):
        resolve_dispatch_target(command_text="/opc-intel status")


def test_resolve_dispatch_target_allows_intel_refresh_dispatch() -> None:
    target = resolve_dispatch_target(command_text="/opc-intel refresh")

    assert target.skill_id == "workflow-modes"
    assert target.agent == "opc-orchestrator"
    assert target.source_command == "/opc-intel"
    assert target.sub_scenario == "intel-refresh"
    assert target.prompt == "refresh"


def test_dispatch_to_agent_invokes_claude_with_resolved_agent_in_claude_code_runtime(monkeypatch) -> None:
    root = _scratch_path("invoke-agent")
    run_cwd = root / "project"
    run_cwd.mkdir()
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        captured["timeout"] = kwargs.get("timeout")

        class FakeProc:
            returncode = 0
            stdout = "planner ok"
            stderr = ""

        return FakeProc()

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "claude-code")
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="用户登录",
        cwd=run_cwd,
        timeout_seconds=17,
        dry_run=False,
    )

    assert result["skill_id"] == "planning"
    assert result["agent"] == "opc-planner"
    assert result["dispatch_mode"] == "agent"
    assert result["dry_run"] is False
    assert result["returncode"] == 0
    assert result["stdout"] == "planner ok"
    assert result["stderr"] == ""
    assert Path(str(captured["cmd"][0])).name.startswith("claude")
    assert captured["cmd"][1:4] == ["--print", "--agent", "opc-planner"]
    assert captured["cmd"][4] == "用户登录"
    assert captured["cwd"] == str(run_cwd)
    assert captured["timeout"] == 17


def test_dispatch_to_agent_installs_project_agent_from_source_in_claude_code_runtime(monkeypatch) -> None:
    root = _scratch_path("install-agent")
    run_cwd = root / "project"
    run_cwd.mkdir()

    def installed_paths(agent: str, cwd: Path):
        return [
            ("project", cwd / ".claude" / "agents" / f"{agent}.md"),
            ("user", root / "home" / ".claude" / "agents" / f"{agent}.md"),
        ]

    def fake_run(cmd, **kwargs):
        class FakeProc:
            returncode = 0
            stdout = "planner ok"
            stderr = ""

        return FakeProc()

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "claude-code")
    monkeypatch.setattr("engine.skill_dispatcher._installed_agent_paths", installed_paths)
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="用户登录",
        cwd=run_cwd,
        dry_run=False,
    )

    installed = run_cwd / ".claude" / "agents" / "opc-planner.md"
    assert installed.exists()
    assert result["success"] is True
    assert result["agent_install_source"] == "source-copy"
    assert result["agent_install_path"] == str(installed)


def test_dispatch_to_agent_uses_codex_runtime_without_claude_shell_dispatch(monkeypatch) -> None:
    root = _scratch_path("codex-runtime")
    run_cwd = root / "project"
    run_cwd.mkdir()

    def fake_run(cmd, **kwargs):
        raise AssertionError("Codex runtime must not call an external agent CLI")

    def fail_claude_command() -> str:
        raise AssertionError("Codex runtime must not resolve the Claude CLI")

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "codex")
    monkeypatch.setattr("engine.skill_dispatcher._claude_command", fail_claude_command)
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="鐢ㄦ埛鐧诲綍",
        cwd=run_cwd,
        dry_run=False,
    )

    assert result["success"] is False
    assert result["status"] == "handoff"
    assert result["executed"] is False
    assert result["runtime"] == "codex"
    assert result["dispatch_mode"] == "codex-native"
    assert result["handoff_only"] is True
    assert result["codex_agent"] == "planner"
    assert result["handoff"]["superopc_agent"] == "opc-planner"
    assert result["handoff"]["codex_agent"] == "planner"
    assert not (run_cwd / ".claude").exists()
    assert not (run_cwd / ".codex").exists()


def test_dispatch_to_agent_runs_codex_exec_when_explicitly_requested(monkeypatch) -> None:
    root = _scratch_path("codex-exec-runtime")
    run_cwd = root / "project"
    run_cwd.mkdir()
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured["cwd"] = kwargs.get("cwd")
        captured["env"] = kwargs.get("env")
        captured["stdin"] = kwargs.get("stdin")
        captured["input"] = kwargs.get("input")

        class FakeProc:
            returncode = 0
            stdout = "codex agent ok"
            stderr = ""

        return FakeProc()

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "codex-exec")
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="plan login",
        cwd=run_cwd,
        timeout_seconds=31,
        dry_run=False,
    )

    cmd = captured["cmd"]
    assert isinstance(cmd, list)
    assert Path(str(cmd[0])).name.startswith("codex")
    assert cmd[1:4] == ["exec", "-C", str(run_cwd)]
    assert "--full-auto" in cmd
    assert cmd[-1] == "-"
    assert "agents/opc-planner.md" in captured["input"]
    assert "plan login" in captured["input"]
    assert captured["cwd"] == str(run_cwd)
    assert captured["env"]["SUPEROPC_AGENT_RUNTIME"] == "codex"
    assert captured["stdin"] is None
    assert result["success"] is True
    assert result["executed"] is True
    assert result["runtime"] == "codex-exec"
    assert result["dispatch_mode"] == "codex-exec"
    assert result["agent"] == "opc-planner"
    assert result["stdout"] == "codex agent ok"
    assert not (run_cwd / ".claude").exists()


def test_dispatch_to_agent_journals_codex_handoff_for_project_trace(monkeypatch) -> None:
    root = _scratch_path("codex-trace")
    run_cwd = root / "project"
    (run_cwd / ".opc").mkdir(parents=True)

    def fake_run(cmd, **kwargs):
        raise AssertionError("Codex runtime must not call an external agent CLI")

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "codex")
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        command_text="/opc-cruise --mode watch --hours 1",
        prompt="trace the workflow handoff",
        cwd=run_cwd,
        dry_run=False,
    )

    assert result["status"] == "handoff"
    handoff_file = Path(result["handoff_file"])
    assert handoff_file.exists()
    assert handoff_file.parent == run_cwd / ".opc" / "agent-handoffs"

    saved = json.loads(handoff_file.read_text(encoding="utf-8"))
    assert saved["skill_id"] == "autonomous-ops"
    assert saved["agent"] == "opc-cruise-operator"
    assert saved["source_command"] == "/opc-cruise"
    assert saved["sub_scenario"] == "cruise-start"
    assert saved["handoff"]["superopc_agent"] == "opc-cruise-operator"

    events = "\n".join(
        path.read_text(encoding="utf-8")
        for path in (run_cwd / ".opc" / "events").glob("events-*.jsonl")
    )
    assert '"topic": "skill.routed"' in events
    assert '"topic": "agent.workflow.requested"' in events
    assert '"topic": "agent.workflow.handoff"' in events
    assert "opc-cruise-operator" in events


def test_dispatch_to_agent_treats_empty_claude_output_as_failure_in_claude_code_runtime(monkeypatch) -> None:
    root = _scratch_path("empty-output")
    run_cwd = root / "project"
    run_cwd.mkdir()

    def fake_run(cmd, **kwargs):
        class FakeProc:
            returncode = 0
            stdout = ""
            stderr = ""

        return FakeProc()

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "claude-code")
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="用户登录",
        cwd=run_cwd,
        dry_run=False,
    )

    assert result["success"] is False
    assert result["returncode"] == 0
    assert result["error"] == "Claude returned no output"


def test_dispatch_to_agent_requests_utf8_subprocess_text_in_claude_code_runtime(monkeypatch) -> None:
    root = _scratch_path("utf8-output")
    run_cwd = root / "project"
    run_cwd.mkdir()
    captured: dict[str, object] = {}

    def fake_run(cmd, **kwargs):
        captured.update(kwargs)

        class FakeProc:
            returncode = 0
            stdout = "计划完成"
            stderr = ""

        return FakeProc()

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "claude-code")
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="用户登录",
        cwd=run_cwd,
        dry_run=False,
    )

    assert result["success"] is True
    assert result["stdout"] == "计划完成"
    assert captured["encoding"] == "utf-8"
    assert captured["errors"] == "replace"


def test_dispatch_to_agent_surfaces_file_not_found_in_claude_code_runtime(monkeypatch) -> None:
    root = _scratch_path("missing-claude")
    run_cwd = root / "project"
    run_cwd.mkdir()

    def fake_run(cmd, **kwargs):
        raise FileNotFoundError("claude not found")

    monkeypatch.setenv("SUPEROPC_AGENT_RUNTIME", "claude-code")
    monkeypatch.setattr("engine.skill_dispatcher.subprocess.run", fake_run)

    result = dispatch_to_agent(
        skill_id="planning",
        prompt="用户登录",
        cwd=run_cwd,
        dry_run=False,
    )

    assert result["success"] is False
    assert result["dispatch_mode"] == "agent"
    assert result["agent"] == "opc-planner"
    assert "claude" in result["error"].lower()
