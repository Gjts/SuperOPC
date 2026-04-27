"""
skill_dispatcher.py - Runtime dispatcher for SuperOPC dispatcher skills.

Resolves either a dispatcher skill id or a slash command into the owning agent,
then routes the handoff to the active host runtime.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from engine.agent_runtime import (
    AGENT_RUNTIME_CODEX,
    build_codex_handoff,
    detect_agent_runtime,
)

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SKILLS_REGISTRY = REPO_ROOT / "skills" / "registry.json"
COMMANDS_DIR = REPO_ROOT / "commands" / "opc"
AGENTS_SOURCE_DIR = REPO_ROOT / "agents"
DEFAULT_TIMEOUT_SECONDS = 600


@dataclass(frozen=True)
class DispatchTarget:
    skill_id: str
    agent: str
    prompt: str
    source_command: str | None = None
    sub_scenario: str | None = None


def _load_skills() -> dict[str, dict[str, Any]]:
    payload = json.loads(SKILLS_REGISTRY.read_text(encoding="utf-8"))
    skills = payload.get("skills", [])
    return {skill["id"]: skill for skill in skills if isinstance(skill, dict) and skill.get("id")}


def _require_dispatcher_skill(skill_id: str) -> dict[str, Any]:
    skills = _load_skills()
    skill = skills.get(skill_id)
    if not skill:
        raise ValueError(f"Unknown skill: {skill_id}")
    if skill.get("type") != "dispatcher":
        raise ValueError(f"Skill '{skill_id}' is not a dispatcher skill")

    agent = skill.get("dispatches_to")
    if not agent:
        raise ValueError(f"Dispatcher skill '{skill_id}' is missing dispatches_to")
    return skill


def _resolve_command_doc(command_name: str) -> Path:
    if command_name == "/opc":
        stem = "opc"
    elif command_name.startswith("/opc-"):
        stem = command_name[len("/opc-"):]
    else:
        raise ValueError(f"Unsupported slash command: {command_name}")

    doc_path = COMMANDS_DIR / f"{stem}.md"
    if not doc_path.exists():
        raise ValueError(f"Command contract not found for {command_name}: {doc_path}")
    return doc_path


def _extract_dispatcher_from_doc(doc_path: Path, command_args: str = "") -> tuple[str, str | None]:
    content = doc_path.read_text(encoding="utf-8")
    if doc_path.stem == "intel":
        subcommand = command_args.split(maxsplit=1)[0].lower() if command_args.strip() else ""
        if subcommand != "refresh":
            raise ValueError("/opc-intel dispatch is only valid for refresh; use local runtime for status/query/validate/snapshot/diff")

    skills = _load_skills()
    ordered_refs = re.findall(r"`([a-z0-9-]+)`", content, re.IGNORECASE)
    matches = [
        skill_id
        for skill_id in ordered_refs
        if skills.get(skill_id, {}).get("type") == "dispatcher"
    ]
    if not matches:
        raise ValueError(f"No dispatcher skill referenced in command contract: {doc_path}")
    skill_id = matches[0]
    sub_scenario_match = re.search(r"`sub_scenario=([a-z0-9_-]+)`", content, re.IGNORECASE)
    sub_scenario = sub_scenario_match.group(1) if sub_scenario_match else None
    return skill_id, sub_scenario


def _parse_command_text(command_text: str) -> tuple[str, str]:
    cleaned = command_text.strip()
    if not cleaned:
        raise ValueError("--command requires slash command text")
    if not cleaned.startswith("/"):
        raise ValueError(f"Command must start with '/': {cleaned}")

    parts = cleaned.split(maxsplit=1)
    command_name = parts[0]
    prompt = parts[1].strip() if len(parts) > 1 else ""
    return command_name, prompt


def resolve_dispatch_target(*, skill_id: str | None = None, command_text: str | None = None, prompt: str = "") -> DispatchTarget:
    if bool(skill_id) == bool(command_text):
        raise ValueError("Provide exactly one of --skill or --command")

    if skill_id:
        skill = _require_dispatcher_skill(skill_id)
        return DispatchTarget(
            skill_id=skill_id,
            agent=str(skill["dispatches_to"]),
            prompt=prompt.strip(),
        )

    command_name, command_prompt = _parse_command_text(command_text or "")
    doc_path = _resolve_command_doc(command_name)
    resolved_skill_id, sub_scenario = _extract_dispatcher_from_doc(doc_path, command_prompt)
    skill = _require_dispatcher_skill(resolved_skill_id)
    combined_prompt = " ".join(part for part in [command_prompt, prompt.strip()] if part).strip()
    return DispatchTarget(
        skill_id=resolved_skill_id,
        agent=str(skill["dispatches_to"]),
        prompt=combined_prompt,
        source_command=command_name,
        sub_scenario=sub_scenario,
    )


def _build_agent_prompt(target: DispatchTarget) -> str:
    if not target.source_command and not target.sub_scenario:
        return target.prompt

    lines: list[str] = []
    if target.source_command:
        lines.append(f"Slash command: {target.source_command}")
    if target.sub_scenario:
        lines.append(f"sub_scenario={target.sub_scenario}")
    if target.prompt:
        lines.append("")
        lines.append(target.prompt)
    return "\n".join(lines).strip()


def _find_source_agent(agent: str) -> Path | None:
    for base_dir in (
        AGENTS_SOURCE_DIR,
        AGENTS_SOURCE_DIR / "domain",
        AGENTS_SOURCE_DIR / "matrix",
    ):
        candidate = base_dir / f"{agent}.md"
        if candidate.exists():
            return candidate
    return None


def _installed_agent_paths(agent: str, cwd: Path) -> list[tuple[str, Path]]:
    return [
        ("project", cwd / ".claude" / "agents" / f"{agent}.md"),
        ("user", Path.home() / ".claude" / "agents" / f"{agent}.md"),
    ]


def ensure_agent_available(agent: str, cwd: Path) -> dict[str, str]:
    for install_source, installed_path in _installed_agent_paths(agent, cwd):
        if installed_path.exists():
            return {
                "agent_install_source": install_source,
                "agent_install_path": str(installed_path),
            }

    source_path = _find_source_agent(agent)
    if source_path is None:
        raise ValueError(f"Agent source not found for {agent}")

    target_path = cwd / ".claude" / "agents" / f"{agent}.md"
    target_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(source_path, target_path)
    return {
        "agent_install_source": "source-copy",
        "agent_install_path": str(target_path),
    }


def _claude_command() -> str:
    configured = os.environ.get("SUPEROPC_CLAUDE_BIN")
    if configured:
        return configured
    return shutil.which("claude") or "claude"


def dispatch_to_agent(
    *,
    skill_id: str | None = None,
    command_text: str | None = None,
    prompt: str = "",
    cwd: Path | None = None,
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS,
    dry_run: bool = False,
) -> dict[str, Any]:
    target = resolve_dispatch_target(skill_id=skill_id, command_text=command_text, prompt=prompt)
    agent_prompt = _build_agent_prompt(target)
    payload: dict[str, Any] = {
        "skill_id": target.skill_id,
        "agent": target.agent,
        "dispatch_mode": "agent",
        "dry_run": dry_run,
        "prompt": target.prompt,
    }
    if target.source_command:
        payload["source_command"] = target.source_command
    if target.sub_scenario:
        payload["sub_scenario"] = target.sub_scenario

    if dry_run:
        return payload

    run_cwd_path = (cwd or REPO_ROOT).resolve()
    try:
        runtime = detect_agent_runtime()
        payload["runtime"] = runtime
        if runtime == AGENT_RUNTIME_CODEX:
            payload.update(
                build_codex_handoff(
                    agent=target.agent,
                    prompt=agent_prompt,
                    source="skill-dispatcher",
                    cwd=run_cwd_path,
                )
            )
            return payload

        payload.update(ensure_agent_available(target.agent, run_cwd_path))
        proc = subprocess.run(
            [_claude_command(), "--print", "--agent", target.agent, agent_prompt],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=timeout_seconds,
            cwd=str(run_cwd_path),
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        empty_stdout = not stdout.strip()
        payload.update(
            {
                "success": proc.returncode == 0 and not empty_stdout,
                "returncode": proc.returncode,
                "stdout": stdout,
                "stderr": stderr,
            }
        )
        if proc.returncode == 0 and empty_stdout:
            payload["error"] = "Claude returned no output"
        return payload
    except FileNotFoundError:
        payload.update(
            {
                "success": False,
                "error": "'claude' CLI not found - cannot dispatch agent",
            }
        )
        return payload
    except subprocess.TimeoutExpired:
        payload.update(
            {
                "success": False,
                "error": f"Agent {target.agent} timed out after {timeout_seconds}s",
            }
        )
        return payload
    except Exception as exc:
        payload.update(
            {
                "success": False,
                "error": str(exc),
            }
        )
        return payload
