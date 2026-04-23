#!/usr/bin/env python3
"""
intel_engine.py - Codebase intelligence for SuperOPC v2.

Maintains a queryable knowledge base about the current project in .opc/intel/.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from engine.event_bus import EventBus, get_event_bus
from engine.intel_builders import (
    build_api_map_index,
    build_arch_decisions_index,
    build_dependency_graph_index,
    build_file_roles_index,
    build_stack_index,
)
from engine.intel_helpers import (
    disabled_payload,
    diff_intel_snapshot,
    query_intel_dir,
    safe_read_json,
    status_for_intel_dir,
    take_snapshot,
    validate_intel_dir,
    write_intel_payload,
)


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
            return True
        try:
            config = json.loads(config_file.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return True

        intel_cfg = config.get("intel", {})
        return intel_cfg.get("enabled", True) if isinstance(intel_cfg, dict) else True

    def query(self, term: str) -> dict[str, Any]:
        if not self.is_enabled():
            return disabled_payload()
        return query_intel_dir(self._intel_dir, term)

    def status(self) -> dict[str, Any]:
        if not self.is_enabled():
            return disabled_payload()
        return status_for_intel_dir(self._intel_dir)

    def diff(self) -> dict[str, Any]:
        if not self.is_enabled():
            return disabled_payload()
        return diff_intel_snapshot(self._intel_dir)

    def write_intel(self, key: str, data: dict[str, Any]) -> Path | None:
        written = write_intel_payload(self._intel_dir, key, data)
        if written is None:
            return None

        filepath, version = written
        self._bus.publish(
            "intel.updated",
            {"file": filepath.name, "version": version},
            source="intel_engine",
        )
        return filepath

    def take_snapshot(self) -> Path:
        return take_snapshot(self._intel_dir)

    def refresh(self) -> dict[str, Any]:
        if not self.is_enabled():
            return disabled_payload()

        files = build_file_roles_index(self._project)
        indexes = {
            "stack": build_stack_index(self._project),
            "files": files,
            "apis": build_api_map_index(self._project),
            "deps": build_dependency_graph_index(self._project),
            "arch": build_arch_decisions_index(self._project, files),
        }

        written: dict[str, str] = {}
        for key, payload in indexes.items():
            path = self.write_intel(key, payload)
            if path is not None:
                written[key] = str(path)

        snapshot = self.take_snapshot()
        validation = self.validate()
        return {
            "ok": validation.get("valid", False),
            "written": written,
            "snapshot": str(snapshot),
            "validation": validation,
        }

    def validate(self) -> dict[str, Any]:
        if not self.is_enabled():
            return disabled_payload()
        return validate_intel_dir(self._intel_dir)

    @staticmethod
    def _safe_read_json(filepath: Path) -> dict[str, Any] | None:
        return safe_read_json(filepath)
