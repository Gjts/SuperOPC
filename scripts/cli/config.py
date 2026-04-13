"""
config.py — Config domain operations for opc-tools.

Manages .opc/config.json: get, set, list keys, build-new-project.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from cli.core import (
    CONFIG_DEFAULTS,
    error,
    load_config,
    opc_dir,
    output,
)


# ---------------------------------------------------------------------------
# Valid config keys
# ---------------------------------------------------------------------------

VALID_CONFIG_KEYS: set[str] = {
    "mode", "granularity", "parallelization", "commit_docs", "model_profile",
    "search_gitignored",
    "workflow.research", "workflow.plan_check", "workflow.verifier",
    "workflow.nyquist_validation", "workflow.auto_advance",
    "workflow.node_repair", "workflow.node_repair_budget",
    "workflow.code_review", "workflow.code_review_depth",
    "workflow.subagent_timeout",
    "git.branching_strategy", "git.base_branch",
    "git.phase_branch_template", "git.milestone_branch_template",
    "git.quick_branch_template",
    "project_code", "phase_naming", "response_language",
}

CONFIG_KEY_SUGGESTIONS: dict[str, str] = {
    "workflow.research_enabled": "workflow.research",
    "workflow.codereview": "workflow.code_review",
    "workflow.review": "workflow.code_review",
    "workflow.review_depth": "workflow.code_review_depth",
}


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def dispatch_config(args: list[str], cwd: Path, raw: bool) -> None:
    """Route config subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "get":
        cmd_config_get(cwd, rest[0] if rest else None, raw)
    elif sub == "set":
        if len(rest) < 2:
            error("config set requires <key> <value>")
        cmd_config_set(cwd, rest[0], rest[1], raw)
    elif sub == "list":
        cmd_config_list(raw)
    elif sub == "defaults":
        cmd_config_defaults(raw)
    elif sub == "build-new-project":
        cmd_config_build_new(cwd, raw)
    else:
        error(f"Unknown config subcommand: {sub}\nAvailable: get, set, list, defaults, build-new-project")


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_config_get(cwd: Path, key: str | None, raw: bool) -> None:
    """Get full config or a specific key (supports dotted paths)."""
    config = load_config(cwd)

    if not key:
        output(config, raw, json.dumps(config, ensure_ascii=False, indent=2))
        return

    value = _resolve_dotted(config, key)
    if value is None:
        suggestion = CONFIG_KEY_SUGGESTIONS.get(key)
        msg = f"Unknown config key: {key}"
        if suggestion:
            msg += f". Did you mean {suggestion}?"
        output({"error": msg}, raw, "")
    else:
        output({key: value}, raw, str(value))


def cmd_config_set(cwd: Path, key: str, value: str, raw: bool) -> None:
    """Update a config value."""
    if not _is_valid_key(key):
        suggestion = CONFIG_KEY_SUGGESTIONS.get(key)
        msg = f"Unknown config key: {key}"
        if suggestion:
            msg += f". Did you mean {suggestion}?"
        error(msg)

    config_path = opc_dir(cwd) / "config.json"

    config: dict[str, Any] = {}
    if config_path.exists():
        try:
            config = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    # Parse value type
    parsed = _parse_value(value)

    # Set via dotted path
    _set_dotted(config, key, parsed)

    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")
    output({"key": key, "value": parsed, "updated": True}, raw, "true")


def cmd_config_list(raw: bool) -> None:
    """List all valid config keys."""
    keys = sorted(VALID_CONFIG_KEYS)
    output({"keys": keys, "count": len(keys)}, raw, "\n".join(keys))


def cmd_config_defaults(raw: bool) -> None:
    """Output default config values."""
    output(CONFIG_DEFAULTS, raw, json.dumps(CONFIG_DEFAULTS, ensure_ascii=False, indent=2))


def cmd_config_build_new(cwd: Path, raw: bool) -> None:
    """Build a fully-materialized config for a new project."""
    config = {
        **CONFIG_DEFAULTS,
        "git": {**CONFIG_DEFAULTS.get("git", {})},
        "workflow": {**CONFIG_DEFAULTS.get("workflow", {})},
    }
    output(config, raw, json.dumps(config, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _is_valid_key(key: str) -> bool:
    """Check if a config key is valid."""
    if key in VALID_CONFIG_KEYS:
        return True
    # Allow dynamic namespaces
    import re
    if re.match(r"^agent_skills\.[a-zA-Z0-9_-]+$", key):
        return True
    if re.match(r"^features\.[a-zA-Z0-9_]+$", key):
        return True
    return False


def _resolve_dotted(obj: dict[str, Any], key: str) -> Any:
    """Resolve a dotted key path like 'workflow.research' in a nested dict."""
    parts = key.split(".")
    current: Any = obj
    for part in parts:
        if isinstance(current, dict) and part in current:
            current = current[part]
        else:
            return None
    return current


def _set_dotted(obj: dict[str, Any], key: str, value: Any) -> None:
    """Set a value at a dotted key path, creating nested dicts as needed."""
    parts = key.split(".")
    current = obj
    for part in parts[:-1]:
        if part not in current or not isinstance(current[part], dict):
            current[part] = {}
        current = current[part]
    current[parts[-1]] = value


def _parse_value(value: str) -> Any:
    """Parse a string value into its most likely type."""
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if value.lower() == "null":
        return None
    try:
        return int(value)
    except ValueError:
        pass
    try:
        return float(value)
    except ValueError:
        pass
    return value
