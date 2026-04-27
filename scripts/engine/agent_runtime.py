"""
Host-aware agent runtime helpers for SuperOPC.

The Python runtime can invoke Claude Code through its CLI, but Codex native
subagents are owned by the current Codex host session. In Codex, SuperOPC must
emit an explicit handoff instead of launching Claude.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Mapping

AGENT_RUNTIME_CODEX = "codex"
AGENT_RUNTIME_CLAUDE_CODE = "claude-code"

_RUNTIME_ALIASES = {
    "auto": "auto",
    "claude": AGENT_RUNTIME_CLAUDE_CODE,
    "claude-code": AGENT_RUNTIME_CLAUDE_CODE,
    "claudecode": AGENT_RUNTIME_CLAUDE_CODE,
    "codex": AGENT_RUNTIME_CODEX,
    "codex-cli": AGENT_RUNTIME_CODEX,
    "openai-codex": AGENT_RUNTIME_CODEX,
}

_CODEX_ENV_MARKERS = (
    "CODEX_THREAD_ID",
    "CODEX_MANAGED_BY_NPM",
    "CODEX_SANDBOX_NETWORK_DISABLED",
)

_CLAUDE_CODE_ENV_MARKERS = (
    "CLAUDE_CODE",
    "CLAUDECODE",
    "CLAUDE_SESSION_ID",
)

CODEX_AGENT_ROLE_MAP = {
    "opc-orchestrator": "planner",
    "opc-planner": "planner",
    "opc-plan-checker": "planner",
    "opc-assumptions-analyzer": "analyst",
    "opc-executor": "executor",
    "opc-reviewer": "code-reviewer",
    "opc-verifier": "verifier",
    "opc-debugger": "debugger",
    "opc-security-auditor": "security-reviewer",
    "opc-business-advisor": "analyst",
    "opc-shipper": "git-master",
    "opc-researcher": "researcher",
    "opc-doc-writer": "writer",
    "opc-doc-verifier": "verifier",
    "opc-codebase-mapper": "explore",
    "opc-ui-auditor": "designer",
    "opc-roadmapper": "planner",
    "opc-session-manager": "planner",
    "opc-cruise-operator": "planner",
    "opc-intel-updater": "explore",
    "opc-frontend-wizard": "executor",
    "opc-backend-architect": "architect",
    "opc-devops-automator": "executor",
    "opc-seo-specialist": "researcher",
    "opc-content-creator": "writer",
    "opc-growth-hacker": "analyst",
    "opc-pricing-analyst": "analyst",
}


def detect_agent_runtime(env: Mapping[str, str] | None = None) -> str:
    """Return the host agent runtime SuperOPC should target."""
    active_env = os.environ if env is None else env
    configured = (
        active_env.get("SUPEROPC_AGENT_RUNTIME")
        or active_env.get("SUPEROPC_AGENT_BACKEND")
        or "auto"
    ).strip().lower()
    runtime = _RUNTIME_ALIASES.get(configured)
    if runtime is None:
        allowed = ", ".join(sorted(_RUNTIME_ALIASES))
        raise ValueError(f"Unsupported agent runtime '{configured}'. Use one of: {allowed}")
    if runtime != "auto":
        return runtime

    if any(active_env.get(marker) for marker in _CODEX_ENV_MARKERS):
        return AGENT_RUNTIME_CODEX
    if any(active_env.get(marker) for marker in _CLAUDE_CODE_ENV_MARKERS):
        return AGENT_RUNTIME_CLAUDE_CODE

    return AGENT_RUNTIME_CLAUDE_CODE


def codex_agent_role(superopc_agent: str) -> str:
    """Map a SuperOPC workflow agent id to the closest Codex native role."""
    role = CODEX_AGENT_ROLE_MAP.get(superopc_agent)
    if role is None:
        raise ValueError(f"No Codex native role mapping for SuperOPC agent '{superopc_agent}'")
    return role


def build_codex_handoff(
    *,
    agent: str,
    prompt: str,
    source: str,
    cwd: Path | None = None,
) -> dict[str, Any]:
    """Build a structured Codex-native handoff without invoking another CLI."""
    role = codex_agent_role(agent)
    handoff: dict[str, Any] = {
        "available": True,
        "runtime": AGENT_RUNTIME_CODEX,
        "source": source,
        "superopc_agent": agent,
        "codex_agent": role,
        "prompt": prompt,
        "instructions": [
            "Use the current Codex host session and the listed Codex native agent role.",
            "Do not launch Claude Code from a Codex runtime.",
        ],
    }
    if cwd is not None:
        handoff["cwd"] = str(cwd)

    return {
        "success": False,
        "status": "handoff",
        "executed": False,
        "runtime": AGENT_RUNTIME_CODEX,
        "dispatch_mode": "codex-native",
        "handoff_only": True,
        "codex_agent": role,
        "handoff": handoff,
        "stdout": f"Codex-native handoff prepared for {agent} via {role}",
    }
