from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from engine.intel_helpers import safe_read_json, safe_read_text


SKIP_DIRS = {".git", "node_modules", "dist", "build", "__pycache__", ".venv", "venv", ".opc"}
SKIP_SUFFIXES = {".pyc", ".pyo", ".pyd", ".png", ".jpg", ".jpeg", ".gif", ".svg", ".ico", ".pdf"}
ROUTE_PATTERNS = (
    ("python", re.compile(r"\b(app|router)\.(get|post|put|delete|patch)\(\s*['\"]([^'\"]+)['\"]", re.IGNORECASE)),
    ("csharp", re.compile(r"\[(HttpGet|HttpPost|HttpPut|HttpDelete|HttpPatch)\((?:\"([^\"]*)\")?\)\]")),
)
COMMAND_PATTERN = re.compile(r"elif command == ['\"]([^'\"]+)['\"]")


def iter_project_files(project_dir: Path):
    for path in project_dir.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SKIP_DIRS for part in path.relative_to(project_dir).parts):
            continue
        if path.suffix.lower() in SKIP_SUFFIXES:
            continue
        yield path


def classify_file_role(project_dir: Path, path: Path) -> str:
    rel_parts = path.relative_to(project_dir).parts
    name = path.name.lower()
    if rel_parts[:2] == ("commands", "opc"):
        return "command"
    if rel_parts and rel_parts[0] == "agents":
        return "agent"
    if name == "skill.md" or (rel_parts and rel_parts[0] == "skills"):
        return "skill"
    if "test" in name or any(part == "tests" for part in rel_parts):
        return "test"
    if name.endswith((".json", ".toml", ".yml", ".yaml")):
        return "config"
    if any(part == "scripts" for part in rel_parts):
        return "script"
    if name.startswith(("main.", "index.", "app.", "server.")):
        return "entry-point"
    if path.suffix.lower() == ".md":
        return "template"
    return "module"


def scan_imports_exports(path: Path) -> tuple[list[str], list[str]]:
    text = safe_read_text(path)
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

    uniq = lambda values: list(dict.fromkeys([value for value in values if value]))
    return uniq(imports), uniq(exports)


def build_stack_index(project_dir: Path) -> dict[str, Any]:
    files = list(iter_project_files(project_dir))
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

    if (project_dir / "scripts" / "engine").is_dir():
        frameworks.append("SuperOPC Engine")
    if (project_dir / "agents").is_dir() and (project_dir / "skills").is_dir():
        frameworks.append("Claude Code plugin content")
    if "pyproject.toml" in names:
        tools.append("pyproject.toml")
    if "pytest.ini" in names or any(path.name.startswith("test_") for path in files):
        tools.append("pytest")
    if (project_dir / ".github" / "workflows").is_dir():
        tools.append("GitHub Actions")

    build_system = "python scripts"
    package_manager = "pip"
    if "package.json" in names:
        build_system += " + npm"
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


def build_file_roles_index(project_dir: Path) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    for path in iter_project_files(project_dir):
        rel = path.relative_to(project_dir).as_posix()
        imports, exports = scan_imports_exports(path)
        entries[rel] = {
            "exports": exports,
            "imports": imports,
            "type": classify_file_role(project_dir, path),
        }
    return {"entries": entries}


def build_api_map_index(project_dir: Path) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    for path in iter_project_files(project_dir):
        rel = path.relative_to(project_dir).as_posix()
        text = safe_read_text(path)
        if not text:
            continue

        for kind, pattern in ROUTE_PATTERNS:
            for match in pattern.finditer(text):
                if kind == "python":
                    method = match.group(2).upper()
                    route = match.group(3)
                else:
                    method = match.group(1).replace("Http", "").upper()
                    route = match.group(2) or ""

                entries[f"{method} {route or rel}"] = {
                    "method": method,
                    "path": route,
                    "params": [],
                    "file": rel,
                    "description": "Detected route declaration",
                }

        for match in COMMAND_PATTERN.finditer(text):
            command = match.group(1)
            entries[f"CLI {command}"] = {
                "method": "CLI",
                "path": command,
                "params": [],
                "file": rel,
                "description": "Detected CLI command dispatch",
            }

    return {"entries": entries}


def build_dependency_graph_index(project_dir: Path) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}

    pyproject = project_dir / "pyproject.toml"
    if pyproject.exists():
        text = safe_read_text(pyproject)
        for dep in re.findall(r'"([A-Za-z0-9_.-]+)(?:[<>=!~].*?)?"', text):
            if dep.lower() in {"python", "setuptools", "wheel"}:
                continue
            entries.setdefault(dep, {"version": "", "type": "production", "used_by": ["pyproject.toml"]})

    requirements = project_dir / "requirements.txt"
    if requirements.exists():
        for line in safe_read_text(requirements).splitlines():
            normalized = line.strip()
            if not normalized or normalized.startswith("#"):
                continue
            dep = re.split(r"[<>=!~\[]", normalized, maxsplit=1)[0].strip()
            if dep:
                entries.setdefault(dep, {"version": "", "type": "production", "used_by": ["requirements.txt"]})

    package_json = safe_read_json(project_dir / "package.json") or {}
    for section, dep_type in (("dependencies", "production"), ("devDependencies", "development"), ("peerDependencies", "peer")):
        for dep, version in package_json.get(section, {}).items():
            entries[dep] = {
                "version": version,
                "type": dep_type,
                "used_by": ["package.json"],
            }

    return {"entries": entries}


def build_arch_decisions_index(project_dir: Path, files: dict[str, Any]) -> dict[str, Any]:
    entries: dict[str, dict[str, Any]] = {}
    decisions: list[tuple[str, str, str, list[str]]] = []

    if (project_dir / "scripts" / "engine").is_dir():
        decisions.append(
            (
                "ARCH-001",
                "Use a Python engine layer for orchestration",
                "scripts/engine/ houses event/state/decision runtime modules",
                ["Keeps orchestration logic in reusable Python modules", "Lets slash-command content stay thin"],
            )
        )
    if (project_dir / "commands" / "opc").is_dir() and (project_dir / "skills").is_dir():
        decisions.append(
            (
                "ARCH-002",
                "Keep slash commands as workflow routers",
                "commands/opc/ delegates behavior to skills, agents, and scripts",
                ["Command docs remain source-of-truth UX contracts", "Runtime behavior is shared through scripts/ and engine modules"],
            )
        )

    file_entries = files.get("entries", {}) if isinstance(files, dict) else {}
    agent_files = [name for name, meta in file_entries.items() if meta.get("type") == "agent"]
    if agent_files:
        decisions.append(
            (
                "ARCH-003",
                "Model specialist behavior as agent content",
                f"Detected {len(agent_files)} agent definition files",
                ["Specialist workflows stay declarative", "Generated integrations can ship the same agent surface"],
            )
        )

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
