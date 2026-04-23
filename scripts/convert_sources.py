from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from convert_runtime_registry import AGENT_DIR, COMMAND_DIR, REPO_ROOT, SKILL_DIRS


@dataclass
class ParsedMarkdown:
    meta: dict[str, Any]
    body: str


@dataclass
class SourceFile:
    kind: str
    path: Path
    relative_path: Path
    parsed: ParsedMarkdown

    @property
    def name(self) -> str:
        raw = self.parsed.meta.get("name")
        return str(raw) if raw else self.path.stem

    @property
    def description(self) -> str:
        raw = self.parsed.meta.get("description")
        return str(raw) if raw else ""


def slugify(name: str) -> str:
    return re.sub(r"(^-|-$)", "", re.sub(r"[^a-z0-9]+", "-", name.lower()))


def parse_inline_list(value: str) -> list[str]:
    inner = value[1:-1].strip()
    if not inner:
        return []
    items = [item.strip() for item in inner.split(",") if item.strip()]
    return [item.strip('"').strip("'") for item in items]


def parse_scalar(value: str) -> Any:
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        return parse_inline_list(value)
    if value == "true":
        return True
    if value == "false":
        return False
    return value.strip('"').strip("'")


def parse_frontmatter(content: str) -> ParsedMarkdown:
    match = re.match(r"^---\n([\s\S]*?)\n---\n([\s\S]*)$", content)
    if not match:
        return ParsedMarkdown(meta={}, body=content)

    meta: dict[str, Any] = {}
    current_key: str | None = None

    for raw_line in match.group(1).splitlines():
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("- ") and current_key and isinstance(meta.get(current_key), list):
            meta[current_key].append(parse_scalar(stripped[2:]))
            continue
        if ":" not in raw_line:
            continue
        key, value = raw_line.split(":", 1)
        key = key.strip()
        value = value.strip()
        if not value:
            meta[key] = []
            current_key = key
            continue
        meta[key] = parse_scalar(value)
        current_key = None

    return ParsedMarkdown(meta=meta, body=match.group(2))


def collect_files(directories: list[str], suffix: str = ".md") -> list[Path]:
    results: list[Path] = []
    for directory in directories:
        abs_dir = REPO_ROOT / directory
        if abs_dir.exists():
            results.extend(sorted(path for path in abs_dir.rglob(f"*{suffix}") if path.is_file()))
    return sorted(results)


def collect_skill_files(directories: list[str]) -> list[Path]:
    """Only match SKILL.md under each skill directory."""
    results: list[Path] = []
    for directory in directories:
        abs_dir = REPO_ROOT / directory
        if abs_dir.exists():
            results.extend(sorted(path for path in abs_dir.rglob("SKILL.md") if path.is_file()))
    return sorted(results)


def collect_skill_assets(directories: list[str]) -> list[Path]:
    """Collect non-SKILL.md markdown assets inside skill directories."""
    results: list[Path] = []
    for directory in directories:
        abs_dir = REPO_ROOT / directory
        if not abs_dir.exists():
            continue
        for md_path in abs_dir.rglob("*.md"):
            if md_path.name != "SKILL.md" and md_path.is_file():
                results.append(md_path)
    return sorted(results)


def collect_sources() -> list[SourceFile]:
    sources: list[SourceFile] = []
    for path in collect_skill_files(SKILL_DIRS):
        sources.append(
            SourceFile(
                "skill",
                path,
                path.relative_to(REPO_ROOT),
                parse_frontmatter(path.read_text(encoding="utf-8")),
            )
        )
    for path in collect_files([AGENT_DIR]):
        sources.append(
            SourceFile(
                "agent",
                path,
                path.relative_to(REPO_ROOT),
                parse_frontmatter(path.read_text(encoding="utf-8")),
            )
        )
    for path in collect_files([COMMAND_DIR]):
        sources.append(
            SourceFile(
                "command",
                path,
                path.relative_to(REPO_ROOT),
                parse_frontmatter(path.read_text(encoding="utf-8")),
            )
        )
    return sources


def extract_tools(source: SourceFile) -> list[str]:
    raw = source.parsed.meta.get("tools")
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str) and raw:
        if raw.startswith("[") and raw.endswith("]"):
            return parse_inline_list(raw)
        return [part.strip() for part in raw.split(",") if part.strip()]
    return []


def map_tools(tools: list[str], mapping: dict[str, str]) -> list[str]:
    mapped: list[str] = []
    for tool in tools:
        mapped_name = mapping.get(tool, tool)
        if mapped_name not in mapped:
            mapped.append(mapped_name)
    return mapped
