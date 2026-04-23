"""
core.py — Shared utilities for SuperOPC CLI.

Provides: output formatting, error handling, path helpers,
config loading, OPC directory resolution, Windows path normalization.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opc_common import write_console_text


# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

_PICK_FIELD: str | None = None


def set_pick_field(field: str | None) -> None:
    """Configure a top-level/dotted field to extract from raw JSON output."""
    global _PICK_FIELD
    _PICK_FIELD = field.strip() if field else None


def output(data: dict[str, Any], raw: bool = False, text: str | None = None) -> None:
    """Print result: JSON when --raw, human-friendly text otherwise."""
    if raw:
        payload = _pick_value(data, _PICK_FIELD) if _PICK_FIELD else data
        rendered = _render_raw_value(payload)
    else:
        rendered = text if text is not None else json.dumps(data, ensure_ascii=False, indent=2)
    write_console_text(rendered, stream=sys.stdout)
    if not rendered.endswith("\n"):
        write_console_text("\n", stream=sys.stdout)
    sys.exit(0)


def error(message: str, code: int = 1) -> None:
    """Print error to stderr and exit."""
    write_console_text(f"opc-tools error: {message}\n", stream=sys.stderr)
    sys.exit(code)


def _pick_value(data: Any, field: str) -> Any:
    value = data
    for segment in field.split("."):
        if isinstance(value, dict) and segment in value:
            value = value[segment]
            continue
        if isinstance(value, list) and segment.isdigit():
            index = int(segment)
            if 0 <= index < len(value):
                value = value[index]
                continue
        error(f"Field not found for --pick: {field}")
    return value


def _render_raw_value(value: Any) -> str:
    if isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=True, indent=None)
    if value is None or isinstance(value, bool):
        return json.dumps(value, ensure_ascii=True)
    return str(value)


# ---------------------------------------------------------------------------
# Path helpers (Windows-safe)
# ---------------------------------------------------------------------------

def to_posix(p: str | Path) -> str:
    """Normalize path to forward slashes."""
    return str(p).replace("\\", "/")


def find_opc_dir(start: Path | None = None) -> Path | None:
    """Walk up from *start* to locate the nearest .opc/ directory."""
    start = start or Path.cwd()
    for candidate in [start] + list(start.parents):
        opc = candidate / ".opc"
        if opc.is_dir():
            return opc
    return None


def opc_root(cwd: Path) -> Path:
    """Return the project root that contains .opc/."""
    opc = find_opc_dir(cwd)
    if opc is None:
        error(f".opc/ directory not found from {cwd}")
    return opc.parent  # type: ignore[union-attr]


def opc_dir(cwd: Path) -> Path:
    """Return the .opc/ directory or exit with error."""
    d = find_opc_dir(cwd)
    if d is None:
        error(f".opc/ directory not found from {cwd}")
    return d  # type: ignore[return-value]


def opc_paths(cwd: Path) -> dict[str, Path]:
    """Standard file paths inside .opc/."""
    d = opc_dir(cwd)
    return {
        "opc": d,
        "project": d / "PROJECT.md",
        "requirements": d / "REQUIREMENTS.md",
        "roadmap": d / "ROADMAP.md",
        "state": d / "STATE.md",
        "config": d / "config.json",
        "phases": d / "phases",
        "research": d / "research",
        "debug": d / "debug",
        "quick": d / "quick",
        "todos": d / "todos",
        "threads": d / "threads",
        "seeds": d / "seeds",
        "handoff": d / "HANDOFF.json",
    }


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG_DEFAULTS: dict[str, Any] = {
    "model_profile": "balanced",
    "commit_docs": True,
    "parallelization": True,
    "search_gitignored": False,
    "granularity": "standard",
    "git": {
        "branching_strategy": "none",
        "base_branch": "main",
        "phase_branch_template": "opc/phase-{phase}-{slug}",
        "milestone_branch_template": "opc/{milestone}-{slug}",
        "quick_branch_template": "opc/quick-{slug}",
    },
    "workflow": {
        "research": True,
        "plan_check": True,
        "verifier": True,
        "nyquist_validation": True,
        "auto_advance": False,
        "node_repair": True,
        "node_repair_budget": 2,
        "code_review": True,
        "code_review_depth": "standard",
    },
    "project_code": None,
    "phase_naming": "sequential",
    "response_language": None,
}


def load_config(cwd: Path) -> dict[str, Any]:
    """Load .opc/config.json merged with defaults."""
    config_path = opc_dir(cwd) / "config.json"
    user: dict[str, Any] = {}
    if config_path.exists():
        try:
            user = json.loads(config_path.read_text(encoding="utf-8"))
        except Exception:
            pass

    merged = {**CONFIG_DEFAULTS, **user}
    # Deep merge nested dicts
    for key in ("git", "workflow"):
        default_sub = CONFIG_DEFAULTS.get(key, {})
        user_sub = user.get(key, {})
        if isinstance(default_sub, dict):
            merged[key] = {**default_sub, **user_sub}
    return merged


# ---------------------------------------------------------------------------
# Git helpers
# ---------------------------------------------------------------------------

def exec_git(cwd: Path, args: list[str]) -> tuple[int, str, str]:
    """Run a git command, return (exit_code, stdout, stderr)."""
    try:
        result = subprocess.run(
            ["git"] + args,
            cwd=str(cwd),
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode, result.stdout.strip(), result.stderr.strip()
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return 1, "", "git not found or timed out"


# ---------------------------------------------------------------------------
# Markdown helpers
# ---------------------------------------------------------------------------

def safe_read(path: Path) -> str:
    """Read file, return empty string on failure."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return ""


def extract_field(content: str, field_name: str) -> str | None:
    """Extract **Field:** value or Field: value from Markdown."""
    escaped = re.escape(field_name)
    bold = re.search(rf"\*\*{escaped}:\*\*\s*(.+)", content, re.IGNORECASE)
    if bold:
        return bold.group(1).strip()
    plain = re.search(rf"^{escaped}:\s*(.+)", content, re.IGNORECASE | re.MULTILINE)
    return plain.group(1).strip() if plain else None


def normalize_phase_name(phase: str) -> str:
    """Normalize phase identifier: '03' → '3', '3.1' → '3.1'."""
    phase = phase.strip()
    # Remove leading zeros but preserve decimals
    parts = phase.split(".")
    parts[0] = str(int(parts[0])) if parts[0].isdigit() else parts[0]
    return ".".join(parts)


def now_iso() -> str:
    """ISO timestamp in UTC."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def generate_slug(text: str) -> str:
    """Convert text to URL-safe slug."""
    slug = re.sub(r"[^a-z0-9]+", "-", text.lower())
    return slug.strip("-")[:60]


# ---------------------------------------------------------------------------
# Phase directory helpers
# ---------------------------------------------------------------------------

def list_phase_dirs(cwd: Path) -> list[Path]:
    """List phase directories sorted numerically."""
    phases_dir = opc_dir(cwd) / "phases"
    if not phases_dir.exists():
        return []
    dirs = [d for d in phases_dir.iterdir() if d.is_dir()]
    return sorted(dirs, key=lambda d: _phase_sort_key(d.name))


def _phase_sort_key(name: str) -> tuple[float, str]:
    """Sort key for phase directory names like '01-setup', '02.1-patch'."""
    match = re.match(r"(\d+(?:\.\d+)?)", name)
    num = float(match.group(1)) if match else 999.0
    return (num, name)


def find_phase_dir(cwd: Path, phase_num: str) -> Path | None:
    """Find a phase directory by number (e.g. '3' finds '03-some-name')."""
    normalized = normalize_phase_name(phase_num)
    for d in list_phase_dirs(cwd):
        match = re.match(r"(\d+(?:\.\d+)?)", d.name)
        if match and normalize_phase_name(match.group(1)) == normalized:
            return d
    return None
