#!/usr/bin/env python3
"""
intel_engine.py — Codebase intelligence for SuperOPC v2.

Maintains a queryable knowledge base about the current project in .opc/intel/.
Five index files:
  - stack.json         — Tech stack detection
  - file-roles.json    — File graph with exports/imports/roles
  - api-map.json       — API surface (routes, endpoints, commands)
  - dependency-graph.json — Dependency chains
  - arch-decisions.json — Architecture decisions and patterns

All JSON files include a _meta object with updated_at and version.
"""

from __future__ import annotations

import json
import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from event_bus import EventBus, get_event_bus


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

INTEL_FILES = {
    "stack": "stack.json",
    "files": "file-roles.json",
    "apis": "api-map.json",
    "deps": "dependency-graph.json",
    "arch": "arch-decisions.json",
}

STALE_SECONDS = 24 * 60 * 60  # 24 hours


# ---------------------------------------------------------------------------
# IntelEngine
# ---------------------------------------------------------------------------

class IntelEngine:
    """Manages codebase intelligence stored in .opc/intel/."""

    def __init__(self, *, project_dir: Path | None = None, bus: EventBus | None = None):
        self._project = project_dir or Path.cwd()
        self._intel_dir = self._project / ".opc" / "intel"
        self._bus = bus or get_event_bus()

    @property
    def intel_dir(self) -> Path:
        return self._intel_dir

    def is_enabled(self) -> bool:
        """Check if intel is enabled via .opc/config.json."""
        config_file = self._project / ".opc" / "config.json"
        if not config_file.exists():
            return True  # Default enabled for SuperOPC (unlike GSD)
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
            intel_cfg = config.get("intel", {})
            return intel_cfg.get("enabled", True)
        except (json.JSONDecodeError, OSError):
            return True

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    def query(self, term: str) -> dict[str, Any]:
        """Search across all intel files for a term (case-insensitive)."""
        if not self.is_enabled():
            return {"disabled": True, "message": "Intel 系统未启用"}

        lower_term = term.lower()
        matches: list[dict[str, Any]] = []
        total = 0

        for key, filename in INTEL_FILES.items():
            filepath = self._intel_dir / filename
            data = self._safe_read_json(filepath)
            if data is None:
                continue

            entries = data.get("entries", data)
            found = self._search_entries(entries, lower_term)
            if found:
                matches.append({"source": filename, "entries": found})
                total += len(found)

        return {"matches": matches, "term": term, "total": total}

    def _search_entries(self, data: Any, lower_term: str) -> list[dict[str, Any]]:
        """Search JSON entries for a term in keys and values."""
        if not isinstance(data, dict):
            return []

        results: list[dict[str, Any]] = []
        for key, value in data.items():
            if key == "_meta":
                continue
            if lower_term in key.lower():
                results.append({"key": key, "value": value})
                continue
            if self._matches_in_value(value, lower_term):
                results.append({"key": key, "value": value})

        return results

    def _matches_in_value(self, value: Any, lower_term: str) -> bool:
        """Recursively check if term appears in any string value."""
        if isinstance(value, str):
            return lower_term in value.lower()
        if isinstance(value, list):
            return any(self._matches_in_value(v, lower_term) for v in value)
        if isinstance(value, dict):
            return any(self._matches_in_value(v, lower_term) for v in value.values())
        return False

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def status(self) -> dict[str, Any]:
        """Report freshness of each intel file."""
        if not self.is_enabled():
            return {"disabled": True, "message": "Intel 系统未启用"}

        now_ts = datetime.now(timezone.utc).timestamp()
        files_status: dict[str, dict[str, Any]] = {}
        overall_stale = False

        for key, filename in INTEL_FILES.items():
            filepath = self._intel_dir / filename
            if not filepath.exists():
                files_status[filename] = {"exists": False, "updated_at": None, "stale": True}
                overall_stale = True
                continue

            data = self._safe_read_json(filepath)
            updated_at = None
            if data and "_meta" in data:
                updated_at = data["_meta"].get("updated_at")

            stale = True
            if updated_at:
                try:
                    ts = datetime.fromisoformat(updated_at.replace("Z", "+00:00")).timestamp()
                    stale = (now_ts - ts) > STALE_SECONDS
                except ValueError:
                    stale = True

            if stale:
                overall_stale = True

            files_status[filename] = {
                "exists": True,
                "updated_at": updated_at,
                "stale": stale,
            }

        return {"files": files_status, "overall_stale": overall_stale}

    # ------------------------------------------------------------------
    # Diff (compare with last snapshot)
    # ------------------------------------------------------------------

    def diff(self) -> dict[str, Any]:
        """Compare current intel files with last snapshot."""
        if not self.is_enabled():
            return {"disabled": True, "message": "Intel 系统未启用"}

        snapshot_file = self._intel_dir / ".last-refresh.json"
        if not snapshot_file.exists():
            return {"error": "无快照记录，请先运行 /opc-intel refresh"}

        try:
            snapshot = json.loads(snapshot_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {"error": "快照文件损坏"}

        changes: dict[str, dict[str, Any]] = {}
        old_hashes = snapshot.get("hashes", {})

        for key, filename in INTEL_FILES.items():
            filepath = self._intel_dir / filename
            current_hash = self._hash_file(filepath) if filepath.exists() else None
            old_hash = old_hashes.get(filename)

            if current_hash and not old_hash:
                changes[filename] = {"status": "added"}
            elif old_hash and not current_hash:
                changes[filename] = {"status": "removed"}
            elif current_hash != old_hash:
                changes[filename] = {"status": "changed"}
            # else: unchanged, skip

        return {"changes": changes, "snapshot_at": snapshot.get("created_at", "unknown")}

    # ------------------------------------------------------------------
    # Write helpers (used by intel-updater agent via scripts)
    # ------------------------------------------------------------------

    def write_intel(self, key: str, data: dict[str, Any]) -> Path | None:
        """Write an intel file with auto-managed _meta."""
        if key not in INTEL_FILES:
            return None

        self._intel_dir.mkdir(parents=True, exist_ok=True)

        if "_meta" not in data:
            data["_meta"] = {}
        data["_meta"]["updated_at"] = _now()
        data["_meta"]["version"] = data["_meta"].get("version", 0) + 1

        filepath = self._intel_dir / INTEL_FILES[key]
        filepath.write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        self._bus.publish(
            "intel.updated",
            {"file": INTEL_FILES[key], "version": data["_meta"]["version"]},
            source="intel_engine",
        )
        return filepath

    def take_snapshot(self) -> Path:
        """Record current state as a snapshot for future diff."""
        self._intel_dir.mkdir(parents=True, exist_ok=True)

        hashes: dict[str, str | None] = {}
        for key, filename in INTEL_FILES.items():
            filepath = self._intel_dir / filename
            hashes[filename] = self._hash_file(filepath) if filepath.exists() else None

        snapshot = {
            "created_at": _now(),
            "hashes": hashes,
        }

        snapshot_file = self._intel_dir / ".last-refresh.json"
        snapshot_file.write_text(
            json.dumps(snapshot, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        return snapshot_file

    def validate(self) -> dict[str, Any]:
        """Validate all intel files for structural correctness."""
        errors: list[str] = []
        valid_count = 0

        for key, filename in INTEL_FILES.items():
            filepath = self._intel_dir / filename
            if not filepath.exists():
                errors.append(f"{filename}: 文件不存在")
                continue

            data = self._safe_read_json(filepath)
            if data is None:
                errors.append(f"{filename}: JSON 解析失败")
                continue

            if "_meta" not in data:
                errors.append(f"{filename}: 缺少 _meta 对象")
            elif "updated_at" not in data["_meta"]:
                errors.append(f"{filename}: _meta 缺少 updated_at")

            if key != "arch" and "entries" not in data:
                errors.append(f"{filename}: 缺少 entries 对象")

            valid_count += 1

        return {
            "valid": len(errors) == 0,
            "files_checked": len(INTEL_FILES),
            "valid_count": valid_count,
            "errors": errors,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _safe_read_json(filepath: Path) -> dict[str, Any] | None:
        try:
            if not filepath.exists():
                return None
            return json.loads(filepath.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None

    @staticmethod
    def _hash_file(filepath: Path) -> str | None:
        try:
            content = filepath.read_bytes()
            return hashlib.sha256(content).hexdigest()
        except OSError:
            return None


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
