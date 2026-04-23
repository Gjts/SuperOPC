from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from opc_common import read_text


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "item"


def write_text(file_path: Path, content: str) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


def parse_frontmatter(markdown: str) -> dict[str, str]:
    if not markdown.startswith("---\n"):
        return {}

    parts = markdown.split("\n---\n", 1)
    if len(parts) != 2:
        return {}

    meta: dict[str, str] = {}
    for line in parts[0].splitlines()[1:]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        meta[key.strip()] = value.strip()
    return meta


def parse_title(markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else "未命名"


def entry_summary(file_path: Path) -> dict[str, str]:
    content = read_text(file_path)
    meta = parse_frontmatter(content)
    return {
        "path": str(file_path),
        "name": meta.get("name", file_path.stem),
        "status": meta.get("status", "UNKNOWN"),
        "updatedAt": meta.get("updatedAt", ""),
        "trigger": meta.get("trigger", ""),
        "title": parse_title(content),
    }


def list_entries(directory: Path) -> list[dict[str, str]]:
    if not directory.exists():
        return []
    return [
        entry_summary(path)
        for path in sorted(directory.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)
    ]


def resolve_existing(directory: Path, raw_name: str) -> Path | None:
    if not directory.exists():
        return None

    query = slugify(raw_name)
    for path in directory.glob("*.md"):
        summary = entry_summary(path)
        if summary["name"] == query:
            return path
        stem = path.stem.lower()
        if stem == query or stem.endswith(f"-{query}"):
            return path
    return None


def next_index(directory: Path, prefix: str) -> int:
    if not directory.exists():
        return 1

    highest = 0
    for path in directory.glob(f"{prefix}-*.md"):
        match = re.match(rf"{re.escape(prefix)}-(\d+)", path.stem)
        if match:
            highest = max(highest, int(match.group(1)))
    return highest + 1
