from __future__ import annotations

import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def _scratch_path(name: str) -> Path:
    root = REPO_ROOT / ".test_tmp" / "dispatch-cli-tests" / f"{name}-{uuid.uuid4().hex}"
    root.mkdir(parents=True, exist_ok=False)
    return root


def _run_cli(
    *args: str,
    cwd: Path = REPO_ROOT,
    env: dict[str, str] | None = None,
) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(REPO_ROOT / "bin" / "opc-tools"),
            "--raw",
            *args,
        ],
        capture_output=True,
        text=True,
        cwd=cwd,
        env=env,
        check=False,
    )


def _write_fake_claude(bin_dir: Path, exit_code: int = 0) -> None:
    if os.name == "nt":
        script = bin_dir / "claude.cmd"
        script.write_text(f"@echo off\necho fake claude ok\nexit /b {exit_code}\n", encoding="utf-8")
        return

    script = bin_dir / "claude"
    script.write_text(f"#!/usr/bin/env sh\necho fake claude ok\nexit {exit_code}\n", encoding="utf-8")
    script.chmod(0o755)


def _write_slow_fake_claude(bin_dir: Path) -> None:
    if os.name == "nt":
        script = bin_dir / "claude.cmd"
        script.write_text("@echo off\nping -n 4 127.0.0.1 >nul\necho late claude\n", encoding="utf-8")
        return

    script = bin_dir / "claude"
    script.write_text("#!/usr/bin/env sh\nsleep 4\necho late claude\n", encoding="utf-8")
    script.chmod(0o755)


def _write_recording_fake_claude(bin_dir: Path, marker: Path, exit_code: int = 0) -> None:
    if os.name == "nt":
        script = bin_dir / "claude.cmd"
        script.write_text(
            f"@echo off\n>> \"{marker}\" echo claude-called\necho fake claude ok\nexit /b {exit_code}\n",
            encoding="utf-8",
        )
        return

    script = bin_dir / "claude"
    script.write_text(
        f"#!/usr/bin/env sh\nprintf 'claude-called\\n' >> \"{marker}\"\necho fake claude ok\nexit {exit_code}\n",
        encoding="utf-8",
    )
    script.chmod(0o755)


def test_dispatch_skill_dry_run_returns_dispatch_metadata() -> None:
    result = _run_cli("dispatch", "--skill", "planning", "--dry-run", "--", "用户登录")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["skill_id"] == "planning"
    assert payload["agent"] == "opc-planner"
    assert payload["dispatch_mode"] == "agent"
    assert payload["dry_run"] is True


def test_dispatch_skill_dry_run_does_not_require_claude() -> None:
    root = _scratch_path("dry-run-no-claude")
    env = os.environ.copy()
    env["PATH"] = str(root)

    result = _run_cli("dispatch", "--skill", "planning", "--dry-run", "--", "用户登录", env=env)

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["dry_run"] is True
    assert payload["agent"] == "opc-planner"


def test_dispatch_command_plan_dry_run_maps_to_planning() -> None:
    result = _run_cli("dispatch", "--command", "/opc-plan 用户登录", "--dry-run")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["skill_id"] == "planning"
    assert payload["agent"] == "opc-planner"
    assert payload["dispatch_mode"] == "agent"
    assert payload["dry_run"] is True


def test_dispatch_command_start_dry_run_maps_to_workflow_modes() -> None:
    result = _run_cli("dispatch", "--command", "/opc-start QuickInvoice", "--dry-run")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["skill_id"] == "workflow-modes"
    assert payload["agent"] == "opc-orchestrator"
    assert payload["dispatch_mode"] == "agent"
    assert payload["dry_run"] is True


def test_dispatch_command_intel_refresh_maps_to_workflow_modes() -> None:
    result = _run_cli("dispatch", "--command", "/opc-intel refresh", "--dry-run")

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["skill_id"] == "workflow-modes"
    assert payload["agent"] == "opc-orchestrator"
    assert payload["sub_scenario"] == "intel-refresh"
    assert payload["prompt"] == "refresh"


def test_dispatch_command_intel_status_stays_out_of_agent_dispatch() -> None:
    result = _run_cli("dispatch", "--command", "/opc-intel status", "--dry-run")

    assert result.returncode != 0
    assert "local runtime" in result.stderr


def test_dispatch_rejects_non_dispatcher_skill() -> None:
    result = _run_cli("dispatch", "--skill", "tdd", "--dry-run", "--", "用户登录")

    assert result.returncode != 0
    assert "not a dispatcher skill" in result.stderr


def test_dispatch_non_dry_run_installs_project_agent_and_calls_claude_in_claude_code_runtime() -> None:
    root = _scratch_path("fake-claude-success")
    fake_bin = root / "bin"
    fake_bin.mkdir()
    _write_fake_claude(fake_bin)
    project = root / "project"
    project.mkdir()
    env = os.environ.copy()
    env["SUPEROPC_AGENT_RUNTIME"] = "claude-code"
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

    result = _run_cli(
        "--cwd",
        str(project),
        "dispatch",
        "--skill",
        "planning",
        "--",
        "用户登录",
        env=env,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is True
    assert payload["stdout"].strip() == "fake claude ok"
    assert payload["agent_install_source"] == "source-copy"
    assert (project / ".claude" / "agents" / "opc-planner.md").exists()


def test_dispatch_non_dry_run_uses_codex_runtime_without_calling_claude() -> None:
    root = _scratch_path("codex-runtime-success")
    fake_bin = root / "bin"
    fake_bin.mkdir()
    marker = root / "claude-called.txt"
    _write_recording_fake_claude(fake_bin, marker)
    project = root / "project"
    project.mkdir()
    env = os.environ.copy()
    env["SUPEROPC_AGENT_RUNTIME"] = "codex"
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

    result = _run_cli(
        "--cwd",
        str(project),
        "dispatch",
        "--skill",
        "planning",
        "--",
        "鐢ㄦ埛鐧诲綍",
        env=env,
    )

    assert result.returncode == 0
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert payload["status"] == "handoff"
    assert payload["executed"] is False
    assert payload["runtime"] == "codex"
    assert payload["dispatch_mode"] == "codex-native"
    assert payload["codex_agent"] == "planner"
    assert payload["handoff"]["superopc_agent"] == "opc-planner"
    assert payload["handoff"]["codex_agent"] == "planner"
    assert "Codex-native handoff prepared" in payload["stdout"]
    assert not marker.exists()
    assert not (project / ".claude").exists()
    assert not (project / ".codex").exists()


def test_dispatch_non_dry_run_failure_exits_nonzero_in_claude_code_runtime() -> None:
    root = _scratch_path("missing-claude")
    project = root / "project"
    project.mkdir()
    env = os.environ.copy()
    env["SUPEROPC_AGENT_RUNTIME"] = "claude-code"
    env["PATH"] = str(root)

    result = _run_cli(
        "--cwd",
        str(project),
        "dispatch",
        "--skill",
        "planning",
        "--",
        "用户登录",
        env=env,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert "claude" in payload["error"].lower()


def test_dispatch_start_timeout_returns_local_runtime_fallback_in_claude_code_runtime() -> None:
    root = _scratch_path("start-timeout-fallback")
    fake_bin = root / "bin"
    fake_bin.mkdir()
    _write_slow_fake_claude(fake_bin)
    project = root / "project"
    project.mkdir()
    env = os.environ.copy()
    env["SUPEROPC_AGENT_RUNTIME"] = "claude-code"
    env["PATH"] = str(fake_bin) + os.pathsep + env.get("PATH", "")

    result = _run_cli(
        "--cwd",
        str(project),
        "dispatch",
        "--command",
        "/opc-start MenuMargin",
        "--timeout",
        "1",
        "--",
        "validation-first restaurant margin project",
        env=env,
    )

    assert result.returncode != 0
    payload = json.loads(result.stdout)
    assert payload["success"] is False
    assert "timed out" in payload["error"]
    fallback = payload["fallback"]
    assert fallback["available"] is True
    assert fallback["workflow"] == "new-project-local-runtime"
    commands = [step["command"] for step in fallback["steps"]]
    assert "init new-project" in commands
    assert "verify health --repair" in commands
    assert "phase add \"<first validation phase>\"" in commands
    assert "template fill verification --phase <N> --name \"<plan name>\"" in commands
