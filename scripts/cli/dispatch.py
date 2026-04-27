"""
dispatch.py - Runtime dispatcher entrypoint for opc-tools.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

from cli.core import error, output
from engine.skill_dispatcher import DEFAULT_TIMEOUT_SECONDS, dispatch_to_agent
from opc_common import write_console_text


def dispatch_dispatch(args: list[str], cwd: Path, raw: bool) -> None:
    try:
        option_args, prompt_args = _split_prompt_args(args)
        parsed = _parse_dispatch_args(option_args)

        timeout_seconds = DEFAULT_TIMEOUT_SECONDS
        timeout_raw = parsed["timeout"]
        if timeout_raw is not None:
            try:
                timeout_seconds = int(timeout_raw)
            except ValueError as exc:
                raise ValueError("--timeout must be an integer number of seconds") from exc
            if timeout_seconds <= 0:
                raise ValueError("--timeout must be greater than zero")

        prompt = " ".join(prompt_args).strip()
        payload = dispatch_to_agent(
            skill_id=parsed["skill"],
            command_text=parsed["command"],
            prompt=prompt,
            cwd=cwd,
            timeout_seconds=timeout_seconds,
            dry_run=bool(parsed["dry-run"]),
        )
    except ValueError as exc:
        error(str(exc))

    if _dispatch_failed(payload):
        _attach_failure_fallback(payload, cwd)
        _exit_failed_dispatch(payload, raw)

    text = payload.get("agent") if payload.get("dry_run") else payload.get("stdout", "")
    output(payload, raw, str(text or ""))


def _split_prompt_args(args: list[str]) -> tuple[list[str], list[str]]:
    if "--" not in args:
        return list(args), []
    idx = args.index("--")
    return list(args[:idx]), list(args[idx + 1 :])


def _parse_dispatch_args(args: list[str]) -> dict[str, str | bool | None]:
    parsed: dict[str, str | bool | None] = {
        "skill": None,
        "command": None,
        "dry-run": False,
        "timeout": None,
    }

    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--dry-run":
            parsed["dry-run"] = True
            i += 1
            continue
        if arg in ("--skill", "--command", "--timeout"):
            if i + 1 >= len(args):
                raise ValueError(f"{arg} requires a value")
            parsed[arg[2:]] = args[i + 1]
            i += 2
            continue
        raise ValueError(f"Unknown dispatch argument: {arg}")

    if bool(parsed["skill"]) == bool(parsed["command"]):
        raise ValueError("dispatch requires exactly one of --skill or --command")
    return parsed


def _dispatch_failed(payload: dict[str, Any]) -> bool:
    if payload.get("dry_run"):
        return False
    if payload.get("status") == "handoff" or payload.get("handoff_only") is True:
        return False
    if payload.get("success") is False:
        return True
    returncode = payload.get("returncode")
    return isinstance(returncode, int) and returncode != 0


def _attach_failure_fallback(payload: dict[str, Any], cwd: Path) -> None:
    if payload.get("fallback"):
        return

    source_command = str(payload.get("source_command") or "")
    sub_scenario = str(payload.get("sub_scenario") or "")
    if source_command != "/opc-start" and sub_scenario != "project-init":
        return

    payload["fallback"] = {
        "available": True,
        "workflow": "new-project-local-runtime",
        "reason": "Agent dispatch failed before completing project startup; continue with local SuperOPC runtime commands.",
        "project_root": str(cwd),
        "steps": [
            {
                "command": "init new-project",
                "purpose": "Load startup context and confirm the project root.",
            },
            {
                "command": "verify health --repair",
                "purpose": "Create or repair the .opc scaffold locally.",
            },
            {
                "command": "phase add \"<first validation phase>\"",
                "purpose": "Create the first roadmap phase and phase directory.",
            },
            {
                "command": "template fill plan --phase <N> --name \"<plan name>\"",
                "purpose": "Create the first plan artifact.",
            },
            {
                "command": "template fill summary --phase <N> --name \"<plan name>\"",
                "purpose": "Create the paired summary artifact.",
            },
            {
                "command": "template fill verification --phase <N> --name \"<plan name>\"",
                "purpose": "Create the paired plan-prefixed verification artifact.",
            },
            {
                "command": "research run --query \"<market or problem query>\"",
                "purpose": "Capture public-source research as weak evidence.",
            },
            {
                "command": "verify health",
                "purpose": "Confirm the local project artifacts are coherent.",
            },
        ],
    }


def _exit_failed_dispatch(payload: dict[str, Any], raw: bool) -> None:
    returncode = payload.get("returncode")
    code = returncode if isinstance(returncode, int) and returncode != 0 else 1
    message = str(payload.get("error") or payload.get("stderr") or "Agent dispatch failed").strip()
    fallback = payload.get("fallback")
    if not raw and isinstance(fallback, dict) and fallback.get("available"):
        steps = fallback.get("steps")
        if isinstance(steps, list) and steps:
            first_step = steps[0]
            if isinstance(first_step, dict) and first_step.get("command"):
                message = f"{message}\nLocal runtime fallback available. Start with: {first_step['command']}"

    if raw:
        rendered = json.dumps(payload, ensure_ascii=True, indent=None)
        write_console_text(rendered + "\n", stream=sys.stdout)
        sys.exit(code)

    error(message, code=code)
