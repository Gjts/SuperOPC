#!/usr/bin/env python3

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from opc_insights import find_opc_dir


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(add_help=True)
    parser.add_argument("--mode", choices=("thread", "seed", "backlog"))
    parser.add_argument("--cwd", default=".")
    parser.add_argument("--trigger", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("entry", nargs="*")
    return parser.parse_args(argv)


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def ensure_opc_dir(start_dir: Path) -> Path:
    opc_dir = find_opc_dir(start_dir)
    if opc_dir is None:
        raise RuntimeError("未找到 .opc/ 目录。请在项目根目录运行，或使用 --cwd 指向包含 .opc 的项目。")
    return opc_dir


def slugify(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return normalized or "item"


def read_text(file_path: Path) -> str:
    try:
        return file_path.read_text(encoding="utf-8")
    except OSError:
        return ""


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
    entries = [entry_summary(path) for path in sorted(directory.glob("*.md"), key=lambda item: item.stat().st_mtime, reverse=True)]
    return entries


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


def create_thread(opc_dir: Path, description: str) -> dict[str, Any]:
    slug = slugify(description)
    file_path = opc_dir / "threads" / f"{slug}.md"
    timestamp = now_iso()
    content = f"""---
name: {slug}
type: thread
status: OPEN
createdAt: {timestamp}
updatedAt: {timestamp}
---

# Thread: {description}

## Goal

{description}

## Context

- 创建于 {timestamp}
- 这是一个跨会话、非阶段绑定的上下文线程

## References

- 暂无

## Next Steps

- 明确下一次恢复时的第一个动作
"""
    write_text(file_path, content)
    return {"created": True, "path": str(file_path), "name": slug, "status": "OPEN"}


def reopen_thread(file_path: Path) -> dict[str, Any]:
    content = read_text(file_path)
    updated = content
    timestamp = now_iso()
    if "status: OPEN" in updated:
        updated = updated.replace("status: OPEN", "status: IN_PROGRESS", 1)
    if re.search(r"^updatedAt: .+$", updated, re.MULTILINE):
        updated = re.sub(r"^updatedAt: .+$", f"updatedAt: {timestamp}", updated, count=1, flags=re.MULTILINE)
    write_text(file_path, updated)
    return {"resumed": True, "path": str(file_path), "content": updated}


def create_seed(opc_dir: Path, idea: str, trigger: str) -> dict[str, Any]:
    directory = opc_dir / "seeds"
    number = next_index(directory, "SEED")
    slug = slugify(idea)
    file_path = directory / f"SEED-{number:03d}-{slug}.md"
    timestamp = now_iso()
    seed_trigger = trigger.strip() or "当路线图进入相关阶段、约束变化或出现明确需求信号时"
    content = f"""---
id: SEED-{number:03d}
name: {slug}
type: seed
status: DORMANT
trigger: {seed_trigger}
createdAt: {timestamp}
updatedAt: {timestamp}
---

# Seed: {idea}

## Why Later

- 现在先记录，不放入当前执行主线

## Trigger

- {seed_trigger}

## References

- 暂无

## First Move When Surfaced

- 先用 `/opc-discuss` 或 `/opc-thread` 澄清范围，再决定是否进入规划
"""
    write_text(file_path, content)
    return {"created": True, "path": str(file_path), "id": f"SEED-{number:03d}", "status": "DORMANT"}


def create_backlog(opc_dir: Path, description: str, note: str) -> dict[str, Any]:
    directory = opc_dir / "todos"
    number = next_index(directory, "BACKLOG")
    slug = slugify(description)
    file_path = directory / f"BACKLOG-{number:03d}-{slug}.md"
    timestamp = now_iso()
    why_later = note.strip() or "当前不进入主路线图，先停放到 backlog。"
    content = f"""---
id: BACKLOG-{number:03d}
name: {slug}
type: backlog
status: PARKED
createdAt: {timestamp}
updatedAt: {timestamp}
---

# Backlog: {description}

## Summary

{description}

## Why Not Now

- {why_later}

## Dependencies / Unknowns

- 暂无

## Promotion Trigger

- 当目标明确、约束已知、值得进入正式规划时

## References

- 暂无

## First Planning Step

- 使用 `/opc-thread` 补全上下文，或直接进入 `/opc-discuss`
"""
    write_text(file_path, content)
    return {"created": True, "path": str(file_path), "id": f"BACKLOG-{number:03d}", "status": "PARKED"}


def format_listing(kind: str, directory: Path, entries: list[dict[str, str]]) -> str:
    title_map = {
        "thread": "SuperOPC Threads",
        "seed": "SuperOPC Seeds",
        "backlog": "SuperOPC Backlog",
    }
    create_hint = {
        "thread": "/opc-thread <description>",
        "seed": "/opc-seed <idea> [--trigger ...]",
        "backlog": "/opc-backlog <description>",
    }
    if not entries:
        return f"{title_map[kind]}\n目录: {directory}\n暂无条目。创建方式: {create_hint[kind]}"

    lines = [title_map[kind], f"目录: {directory}"]
    for item in entries:
        extra = f" · trigger={item['trigger']}" if item["trigger"] else ""
        lines.append(f"- {item['name']} · {item['status']} · {item['updatedAt'] or '未记录'}{extra}")
    return "\n".join(lines)


def format_created(kind: str, payload: dict[str, Any]) -> str:
    title = {
        "thread": "Thread created",
        "seed": "Seed created",
        "backlog": "Backlog item created",
    }[kind]
    lines = [title, f"路径: {payload['path']}"]
    if "name" in payload:
        lines.append(f"名称: {payload['name']}")
    if "id" in payload:
        lines.append(f"编号: {payload['id']}")
    return "\n".join(lines)


def format_existing(kind: str, file_path: Path, content: str) -> str:
    return f"SuperOPC {kind}\n路径: {file_path}\n\n{content.strip()}"


def _emit_write_advisory(kind: str, target_dir: Path) -> None:
    """Stderr 建议：提醒用户"创建模式会写入 .opc/"，符合 v1.4.2 mixed-path 约定。

    v1.4.2 AGENTS.md §Read-only CLI 白名单例外 把 thread/seed/backlog 归类为
    MIXED 路径（列出模式只读、创建模式轻量写入）。这里的 stderr 警告不阻断，
    但让用户在 CLI 快速创建与 agent workflow 创建之间做出知情选择。
    """
    if os.environ.get("OPC_SUPPRESS_WRITE_ADVISORY") == "1":
        return
    sys.stderr.write(
        f"[opc-{kind}] note: about to write to {target_dir}/.\n"
        f"  CLI fast-path is OK for quick capture; for richer items "
        f"(with planner review / agent workflow) use /opc-plan or /opc.\n"
        f"  Set OPC_SUPPRESS_WRITE_ADVISORY=1 to silence this notice.\n"
    )


def handle_thread(opc_dir: Path, entry_text: str, as_json: bool) -> str:
    directory = opc_dir / "threads"
    if not entry_text:
        payload = {"kind": "thread", "items": list_entries(directory), "directory": str(directory)}
        return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_listing("thread", directory, payload["items"])

    existing = resolve_existing(directory, entry_text)
    if existing:
        payload = reopen_thread(existing)
        return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_existing("Thread", existing, payload["content"])

    _emit_write_advisory("thread", directory)
    payload = create_thread(opc_dir, entry_text)
    return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_created("thread", payload)


def handle_seed(opc_dir: Path, entry_text: str, trigger: str, as_json: bool) -> str:
    directory = opc_dir / "seeds"
    if not entry_text:
        payload = {"kind": "seed", "items": list_entries(directory), "directory": str(directory)}
        return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_listing("seed", directory, payload["items"])

    existing = resolve_existing(directory, entry_text)
    if existing:
        content = read_text(existing)
        payload = {"path": str(existing), "content": content}
        return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_existing("Seed", existing, content)

    _emit_write_advisory("seed", directory)
    payload = create_seed(opc_dir, entry_text, trigger)
    return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_created("seed", payload)


def handle_backlog(opc_dir: Path, entry_text: str, note: str, as_json: bool) -> str:
    directory = opc_dir / "todos"
    if not entry_text:
        payload = {"kind": "backlog", "items": list_entries(directory), "directory": str(directory)}
        return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_listing("backlog", directory, payload["items"])

    existing = resolve_existing(directory, entry_text)
    if existing:
        content = read_text(existing)
        payload = {"path": str(existing), "content": content}
        return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_existing("Backlog", existing, content)

    _emit_write_advisory("backlog", directory)
    payload = create_backlog(opc_dir, entry_text, note)
    return json.dumps(payload, ensure_ascii=False, indent=2) if as_json else format_created("backlog", payload)


def run_cli(default_mode: str) -> int:
    try:
        args = parse_args(sys.argv[1:])
        mode = args.mode or default_mode
        entry_text = " ".join(args.entry).strip()
        opc_dir = ensure_opc_dir(Path(args.cwd))

        if mode == "thread":
            output = handle_thread(opc_dir, entry_text, args.json)
        elif mode == "seed":
            output = handle_seed(opc_dir, entry_text, args.trigger, args.json)
        elif mode == "backlog":
            output = handle_backlog(opc_dir, entry_text, args.note, args.json)
        else:
            raise RuntimeError(f"Unsupported mode: {mode}")

        print(output)
        return 0
    except Exception as exc:
        sys.stderr.write(f"SuperOPC context error: {exc}\n")
        return 1


if __name__ == "__main__":
    raise SystemExit(run_cli("thread"))
