from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from opc_common import read_json, read_text


@dataclass
class RoadmapRow:
    phase: str
    completed_plans: int
    total_plans: int
    status: str
    completed_date: str


def read_recent_sessions(sessions_dir: Path, limit: int = 5) -> list[dict[str, Any]]:
    if not sessions_dir.exists():
        return []

    sessions: list[dict[str, Any]] = []
    for session_file in sorted(
        sessions_dir.glob("session-*.json"),
        key=lambda item: item.stat().st_mtime,
        reverse=True,
    ):
        payload = read_json(session_file)
        if payload:
            payload["file"] = str(session_file)
            sessions.append(payload)
        if len(sessions) >= limit:
            break
    return sessions


def get_section(markdown: str, heading: str) -> str:
    pattern = re.compile(
        rf"^#{{2,3}}\s+{re.escape(heading)}\s*$([\s\S]*?)(?=^#{{2,3}}\s+|\Z)",
        re.MULTILINE,
    )
    match = pattern.search(markdown)
    return match.group(1).strip() if match else ""


def extract_first_heading(markdown: str) -> str:
    match = re.search(r"^#\s+(.+)$", markdown, re.MULTILINE)
    return match.group(1).strip() if match else "未命名项目"


def extract_inline_value(markdown: str, label: str) -> str:
    variants = [
        rf"\*\*{re.escape(label)}：\*\*\s*(.+)$",
        rf"\*\*{re.escape(label)}:\*\*\s*(.+)$",
        rf"{re.escape(label)}：\s*(.+)$",
        rf"{re.escape(label)}:\s*(.+)$",
    ]
    for variant in variants:
        match = re.search(variant, markdown, re.MULTILINE)
        if match:
            return match.group(1).strip()
    return ""


def count_checklist_items(markdown: str) -> tuple[int, int]:
    total = len(re.findall(r"^- \[(?: |x)\]\s+", markdown, re.MULTILINE | re.IGNORECASE))
    completed = len(re.findall(r"^- \[x\]\s+", markdown, re.MULTILINE | re.IGNORECASE))
    return total, completed


def parse_roadmap_progress(roadmap_text: str) -> list[RoadmapRow]:
    section = get_section(roadmap_text, "进度")
    rows: list[RoadmapRow] = []

    if not section:
        return rows

    for raw_line in section.splitlines():
        line = raw_line.strip()
        if (
            not line.startswith("|")
            or re.match(r"^(\|\-)+", line)
            or "阶段 | 已完成计划" in line
        ):
            continue

        cells = [cell.strip() for cell in line.split("|")[1:-1]]
        if len(cells) < 4:
            continue

        plan_match = re.search(r"(\d+)\s*/\s*(\d+)", cells[1])
        rows.append(
            RoadmapRow(
                phase=cells[0],
                completed_plans=int(plan_match.group(1)) if plan_match else 0,
                total_plans=int(plan_match.group(2)) if plan_match else 0,
                status=cells[2],
                completed_date=cells[3],
            )
        )

    return rows


def parse_next_roadmap_task(roadmap_text: str) -> str:
    for line in roadmap_text.splitlines():
        if not re.match(r"^- \[ \]", line):
            continue
        if re.search(r"阶段\s+\d", line):
            continue
        return re.sub(r"\*\*", "", re.sub(r"^- \[ \]\s*", "", line)).strip()
    return "未在 ROADMAP.md 中找到未完成计划"


def extract_list_items(section_text: str) -> list[str]:
    if not section_text or "暂无" in section_text:
        return []

    items: list[str] = []
    for raw_line in section_text.splitlines():
        line = raw_line.strip()
        match = re.match(r"^(?:-|\d+\.)\s+(.+)$", line)
        if match:
            items.append(match.group(1).strip())
    return items


def count_files(dir_path: Path) -> int:
    if not dir_path.exists():
        return 0

    total = 0
    for entry in dir_path.iterdir():
        if entry.name.startswith("."):
            continue
        total += count_files(entry) if entry.is_dir() else 1
    return total


def extract_metric(texts: Iterable[str], labels: Iterable[str]) -> str:
    for text in texts:
        if not text:
            continue
        for label in labels:
            variants = [
                rf"^\s*-\s*{re.escape(label)}\s*[:：]\s*(.+)$",
                rf"^\s*\*\*{re.escape(label)}\*\*\s*[:：]\s*(.+)$",
                rf"^\s*{re.escape(label)}\s*[:：]\s*(.+)$",
            ]
            for variant in variants:
                match = re.search(variant, text, re.MULTILINE)
                if match:
                    return match.group(1).strip()
    return "未记录"


def parse_risky_decisions(project_text: str) -> int:
    return sum(
        1
        for line in project_text.splitlines()
        if "|" in line and "⚠️" in line
    )


def parse_state(state_text: str) -> dict[str, Any]:
    phase_match = re.search(r"阶段：\[(.+?)\]\s*/\s*\[(.+?)\]\s*（(.+?)）", state_text)
    plan_match = re.search(r"计划：\[(.+?)\]\s*/\s*\[(.+?)\]\s*", state_text)
    progress_match = re.search(r"进度：.*?(\d+)%", state_text)
    todos = extract_list_items(get_section(state_text, "待办事项"))
    blockers = extract_list_items(get_section(state_text, "阻塞/关注"))

    return {
        "currentFocus": extract_inline_value(state_text, "当前焦点") or "未记录",
        "coreValue": extract_inline_value(state_text, "核心价值") or "未记录",
        "status": extract_inline_value(state_text, "状态") or "未记录",
        "recentActivity": extract_inline_value(state_text, "最近活动") or "未记录",
        "lastSession": extract_inline_value(state_text, "上次会话") or "未记录",
        "stopPoint": extract_inline_value(state_text, "停止于") or "未记录",
        "resumeFile": extract_inline_value(state_text, "恢复文件") or "未记录",
        "phase": (
            {
                "current": phase_match.group(1),
                "total": phase_match.group(2),
                "name": phase_match.group(3),
            }
            if phase_match
            else None
        ),
        "plan": (
            {
                "current": plan_match.group(1),
                "total": plan_match.group(2),
            }
            if plan_match
            else None
        ),
        "progressPercent": int(progress_match.group(1)) if progress_match else None,
        "blockerCount": len(blockers),
        "blockers": blockers,
        "todoCountFromState": len(todos),
        "todos": todos,
    }


def parse_git_info(project_root: Path) -> dict[str, Any]:
    def git_output(args: list[str], *, retry_without_global_excludes: bool = False) -> str:
        try:
            return subprocess.check_output(
                ["git", *args],
                cwd=project_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                stderr=subprocess.DEVNULL,
            )
        except subprocess.CalledProcessError:
            if not retry_without_global_excludes:
                raise
            return subprocess.check_output(
                ["git", "-c", "core.excludesfile=", *args],
                cwd=project_root,
                text=True,
                encoding="utf-8",
                errors="replace",
                stderr=subprocess.DEVNULL,
            )

    try:
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=project_root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True,
        )

        branch = git_output(["branch", "--show-current"]).strip() or "DETACHED"

        status_output = git_output(["status", "--short"], retry_without_global_excludes=True).strip()
        dirty_files = len(status_output.splitlines()) if status_output else 0

        last_commit = git_output(["log", "-1", "--pretty=format:%h %cs %s"]).strip() or "无提交"

        return {
            "available": True,
            "branch": branch,
            "dirtyFiles": dirty_files,
            "lastCommit": last_commit,
        }
    except Exception:
        return {
            "available": False,
            "branch": "未知",
            "dirtyFiles": 0,
            "lastCommit": "不可用",
        }


def parse_validation_debt(
    state_text: str,
    git_info: dict[str, Any],
    warnings: list[str],
    extra_items: list[str] | None = None,
) -> list[str]:
    debt: list[str] = []

    validation_section = get_section(state_text, "验证欠债")
    debt.extend(extract_list_items(validation_section))

    if git_info.get("available") and git_info.get("dirtyFiles", 0) > 0:
        debt.append(f"未提交工作区变更：{git_info['dirtyFiles']} 个文件")

    debt.extend(warnings)
    if extra_items:
        debt.extend(extra_items)

    deduped: list[str] = []
    seen: set[str] = set()
    for item in debt:
        normalized = item.strip()
        if normalized and normalized not in seen:
            deduped.append(normalized)
            seen.add(normalized)
    return deduped
