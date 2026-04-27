from __future__ import annotations

import json
from pathlib import Path

import pytest

from engine.agent_runtime import (
    AGENT_RUNTIME_CLAUDE_CODE,
    AGENT_RUNTIME_CODEX,
    CODEX_AGENT_ROLE_MAP,
    codex_agent_role,
    detect_agent_runtime,
)
from engine.cruise_controller import ACTION_AGENT_MAP

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_detect_agent_runtime_prefers_explicit_override() -> None:
    env = {
        "SUPEROPC_AGENT_RUNTIME": "claude-code",
        "CODEX_THREAD_ID": "codex-thread",
    }

    assert detect_agent_runtime(env) == AGENT_RUNTIME_CLAUDE_CODE


def test_detect_agent_runtime_auto_detects_codex_markers() -> None:
    assert detect_agent_runtime({"CODEX_THREAD_ID": "thread-1"}) == AGENT_RUNTIME_CODEX
    assert detect_agent_runtime({"CODEX_MANAGED_BY_NPM": "1"}) == AGENT_RUNTIME_CODEX


def test_detect_agent_runtime_auto_detects_claude_code_markers() -> None:
    assert detect_agent_runtime({"CLAUDE_SESSION_ID": "session-1"}) == AGENT_RUNTIME_CLAUDE_CODE


def test_detect_agent_runtime_empty_env_does_not_read_process_env(monkeypatch) -> None:
    monkeypatch.setenv("CODEX_THREAD_ID", "process-codex-thread")

    assert detect_agent_runtime({}) == AGENT_RUNTIME_CLAUDE_CODE


def test_detect_agent_runtime_auto_prefers_codex_when_markers_conflict() -> None:
    env = {
        "CODEX_THREAD_ID": "thread-1",
        "CLAUDE_SESSION_ID": "session-1",
    }

    assert detect_agent_runtime(env) == AGENT_RUNTIME_CODEX


def test_detect_agent_runtime_rejects_unknown_override() -> None:
    with pytest.raises(ValueError, match="Unsupported agent runtime"):
        detect_agent_runtime({"SUPEROPC_AGENT_RUNTIME": "unknown-host"})


def test_codex_role_map_covers_dispatchable_agents() -> None:
    skills = json.loads((REPO_ROOT / "skills" / "registry.json").read_text(encoding="utf-8"))
    registry = json.loads((REPO_ROOT / "agents" / "registry.json").read_text(encoding="utf-8"))
    dispatch_agents = {
        skill.get("dispatches_to")
        for skill in skills.get("skills", [])
        if isinstance(skill, dict) and skill.get("dispatches_to")
    }
    dispatch_agents.update(ACTION_AGENT_MAP.values())
    dispatch_agents.update(
        agent.get("id")
        for agent in registry.get("agents", [])
        if isinstance(agent, dict) and agent.get("id")
    )
    dispatch_agents.discard(None)

    missing = sorted(agent for agent in dispatch_agents if agent not in CODEX_AGENT_ROLE_MAP)
    assert missing == []
    assert codex_agent_role("opc-reviewer") == "code-reviewer"
    assert codex_agent_role("opc-security-auditor") == "security-reviewer"


def test_codex_agent_role_rejects_unknown_agents() -> None:
    with pytest.raises(ValueError, match="No Codex native role mapping"):
        codex_agent_role("opc-new-unmapped-agent")
