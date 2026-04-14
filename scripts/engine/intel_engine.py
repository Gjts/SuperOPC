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
import re
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

    def refresh(self) -> dict[str, Any]:
        """Rebuild all intel indexes from the current project and record a snapshot."""
        if not self.is_enabled():
            return {"disabled": True, "message": "Intel 系统未启用"}

        stack = self._build_stack_index()
        files = self._build_file_roles_index()
        apis = self._build_api_map_index()
        deps = self._build_dependency_graph_index()
        arch = self._build_arch_decisions_index(stack, files, apis, deps)

        written: dict[str, str] = {}
        for key, data in (
            ("stack", stack),
            ("files", files),
            ("apis", apis),
            ("deps", deps),
            ("arch", arch),
        ):
            path = self.write_intel(key, data)
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

            if key in {"files", "apis", "deps", "arch"} and "entries" not in data:
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

    def _build_stack_index(self) -> dict[str, Any]:
        files = list(self._iter_project_files())
        suffixes = {path.suffix.lower() for path in files if path.suffix}
        names = {path.name for path in files}

        languages: list[str] = []
        frameworks: list[str] = []
        tools: list[str] = []
        content_formats: list[str] = []

        if ".py" in suffixes:
            languages.append("Python")
        if ".ts" in suffixes or ".tsx" in suffixes:
            languages.append("TypeScript")
        if ".js" in suffixes or ".jsx" in suffixes:
            languages.append("JavaScript")
        if ".cs" in suffixes:
            languages.append("C#")
        if ".md" in suffixes:
            content_formats.append("Markdown")
        if ".json" in suffixes:
            content_formats.append("JSON")

        if (self._project / "scripts" / "engine").is_dir():
            frameworks.append("SuperOPC Engine")
        if (self._project / "agents").is_dir() and (self._project / "skills").is_dir():
            frameworks.append("Claude Code plugin content")
        if "pyproject.toml" in names:
            tools.append("pyproject.toml")
        if "pytest.ini" in names or any(path.name.startswith("test_") for path in files):
            tools.append("pytest")
        if (self._project / ".github" / "workflows").is_dir():
            tools.append("GitHub Actions")

        build_system = "python scripts"
        if "package.json" in names:
            build_system += " + npm"
        package_manager = "pip"
        if "package.json" in names:
            package_manager = "pip + npm"

        return {
            "languages": languages,
            "frameworks": frameworks,
            "tools": tools,
            "build_system": build_system,
            "test_framework": "pytest" if "pytest" in tools else "unknown",
            "package_manager": package_manager,
            "content_formats": content_formats,
        }

    def _build_file_roles_index(self) -> dict[str, Any]:
        entries: dict[str, dict[str, Any]] = {}
        for path in self._iter_project_files():
            rel = path.relative_to(self._project).as_posix()
            role = self._classify_file_role(path)
            imports, exports = self._scan_imports_exports(path)
            entries[rel] = {
                "exports": exports,
                "imports": imports,
                "type": role,
            }
        return {"entries": entries}

    def _build_api_map_index(self) -> dict[str, Any]:
        entries: dict[str, dict[str, Any]] = {}
        route_patterns = [
            re.compile(r"\b(app|router)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE),
            re.compile(r"\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)\((?:\"([^\"]*)\")?\)\]"),
        ]
        command_pattern = re.compile(r"elif command == ['\"]([^'\"]+)['\"]")

        for path in self._iter_project_files():
            rel = path.relative_to(self._project).as_posix()
            text = self._safe_read_text(path)
            if not text:
                continue
            for pattern in route_patterns:
                for match in pattern.finditer(text):
                    if pattern is route_patterns[0]:
                        method = match.group(2).upper()
                        route = match.group(3)
                    else:
                        method = match.group(1).replace("Http", "").upper()
                        route = match.group(2) or ""
                    key = f"{method} {route or rel}"
                    entries[key] = {
                        "method": method,
                        "path": route,
                        "params": [],
                        "file": rel,
                        "description": "Detected route declaration",
                    }
            for match in command_pattern.finditer(text):
                command = match.group(1)
                key = f"CLI {command}"
                entries[key] = {
                    "method": "CLI",
                    "path": command,
                    "params": [],
                    "file": rel,
                    "description": "Detected CLI command dispatch",
                }

        return {"entries": entries}

    def _build_dependency_graph_index(self) -> dict[str, Any]:
        entries: dict[str, dict[str, Any]] = {}

        pyproject = self._project / "pyproject.toml"
        if pyproject.exists():
            text = self._safe_read_text(pyproject)
            for dep in re.findall(r'"([A-Za-z0-9_.-]+)(?:[<>=!~].*?)?"', text):
                if dep.lower() in {"python", "setuptools", "wheel"}:
                    continue
                entries.setdefault(dep, {"version": "", "type": "production", "used_by": ["pyproject.toml"]})

        requirements = self._project / "requirements.txt"
        if requirements.exists():
            for line in self._safe_read_text(requirements).splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                dep = re.split(r"[<>=!~\[]", line, maxsplit=1)[0].strip()
                if dep:
                    entries.setdefault(dep, {"version": "", "type": "production", "used_by": ["requirements.txt"]})

        package_json = self._project / "package.json"
        if package_json.exists():
            try:
                pkg = json.loads(package_json.read_text(encoding="utf-8"))
            except (json.JSONDecodeError, OSError):
                pkg = {}
            for section, dep_type in (("dependencies", "production"), ("devDependencies", "development"), ("peerDependencies", "peer")):
                for dep, version in pkg.get(section, {}).items():
                    entries[dep] = {
                        "version": version,
                        "type": dep_type,
                        "used_by": ["package.json"],
                    }

        return {"entries": entries}

    def _build_arch_decisions_index(
        self,
        stack: dict[str, Any],
        files: dict[str, Any],
        apis: dict[str, Any],
        deps: dict[str, Any],
    ) -> dict[str, Any]:
        entries: dict[str, dict[str, Any]] = {}
        decisions: list[tuple[str, str, str, list[str]]] = []

        if (self._project / "scripts" / "engine").is_dir():
            decisions.append((
                "ARCH-001",
                "Use a Python engine layer for orchestration",
                "scripts/engine/ houses event/state/decision runtime modules",
                ["Keeps orchestration logic in reusable Python modules", "Lets slash-command content stay thin"],
            ))
        if (self._project / "commands" / "opc").is_dir() and (self._project / "skills").is_dir():
            decisions.append((
                "ARCH-002",
                "Keep slash commands as workflow routers",
                "commands/opc/ delegates behavior to skills, agents, and scripts",
                ["Command docs remain source-of-truth UX contracts", "Runtime behavior is shared through scripts/ and engine modules"],
            ))
        if files.get("entries"):
            agent_files = [name for name, meta in files["entries"].items() if meta.get("type") == "agent"]
            if agent_files:
                decisions.append((
                    "ARCH-003",
                    "Model specialist behavior as agent content",
                    f"Detected {len(agent_files)} agent definition files",
                    ["Specialist workflows stay declarative", "Generated integrations can ship the same agent surface"],
                ))

        for decision_id, title, context, consequences in decisions:
            entries[decision_id] = {
                "title": title,
                "status": "accepted",
                "context": context,
                "decision": title,
                "consequences": consequences,
                "file": None,
            }

        return {"entries": entries}

    def _iter_project_files(self):
        skip_dirs = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", ".opc"}
        skip_suffixes = {".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf"}
        for path in self._project.rglob("*"):
            if not path.is_file():
                continue
            if any(part in skip_dirs for part in path.relative_to(self._project).parts):
                continue
            if path.suffix.lower() in skip_suffixes:
                continue
            yield path

    def _classify_file_role(self, path: Path) -> str:
        rel_parts = path.relative_to(self._project).parts
        name = path.name.lower()
        if rel_parts[:2] == ("commands", "opc"):
            return "command"
        if rel_parts and rel_parts[0] == "agents":
            return "agent"
        if name == "skill.md" or (rel_parts and rel_parts[0] == "skills"):
            return "skill"
        if "test" in name or any(part == "tests" for part in rel_parts):
            return "test"
        if name.endswith(".json") or name.endswith(".toml") or name.endswith(".yml") or name.endswith(".yaml"):
            return "config"
        if any(part == "scripts" for part in rel_parts):
            return "script"
        if name.startswith(("main.", "index.", "app.", "server.")):
            return "entry-point"
        if path.suffix.lower() == ".md":
            return "template"
        return "module"

    def _scan_imports_exports(self, path: Path) -> tuple[list[str], list[str]]:
        text = self._safe_read_text(path)
        if not text:
            return [], []

        imports: list[str] = []
        exports: list[str] = []
        for line in text.splitlines():
            stripped = line.strip()
            py_import = re.match(r"(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", stripped)
            if py_import:
                imports.append(py_import.group(1) or py_import.group(2) or "")
                continue
            js_import = re.match(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", stripped)
            if js_import:
                imports.append(js_import.group(1))
                continue
            export_match = re.match(r"export\s+(?:default\s+)?(?:class|function|const|let|var)?\s*([A-Za-z0-9_]+)?", stripped)
            if export_match and export_match.group(1):
                exports.append(export_match.group(1))
                continue
            py_def = re.match(r"def\s+([A-Za-z0-9_]+)\(", stripped)
            if py_def:
                exports.append(py_def.group(1))

        return list(dict.fromkeys([x for x in imports if x])), list(dict.fromkeys([x for x in exports if x]))

    @staticmethod
    def _safe_read_text(path: Path) -> str:
        try:
            return path.read_text(encoding="utf-8")
        except OSError:
            return ""
        except UnicodeDecodeError:
            try:
                return path.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                return ""

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
