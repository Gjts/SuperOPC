"""
template.py — Template domain operations for opc-tools.

Creates pre-filled PLAN.md, SUMMARY.md, and VERIFICATION.md files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from cli.core import (
    error,
    extract_field,
    find_phase_dir,
    generate_slug,
    normalize_phase_name,
    now_iso,
    opc_dir,
    opc_paths,
    output,
    safe_read,
    to_posix,
)


# ---------------------------------------------------------------------------
# Dispatching
# ---------------------------------------------------------------------------

def dispatch_template(args: list[str], cwd: Path, raw: bool) -> None:
    """Route template subcommands."""
    sub = args[0] if args else ""
    rest = args[1:]

    if sub == "fill":
        if not rest:
            error("template type required (plan, summary, verification)")
        template_type = rest[0]
        named = _extract_named(rest[1:], ["phase", "plan", "name", "type", "wave", "fields"])
        cmd_template_fill(cwd, template_type, named, raw)
    elif sub == "select":
        cmd_template_select(cwd, rest[0] if rest else None, raw)
    else:
        error(f"Unknown template subcommand: {sub}\nAvailable: fill, select")


def _extract_named(args: list[str], keys: list[str]) -> dict[str, str | None]:
    result: dict[str, str | None] = {}
    for key in keys:
        flag = f"--{key}"
        try:
            idx = args.index(flag)
            if idx + 1 < len(args) and not args[idx + 1].startswith("--"):
                result[key] = args[idx + 1]
            else:
                result[key] = None
        except ValueError:
            result[key] = None
    return result


# ---------------------------------------------------------------------------
# Commands
# ---------------------------------------------------------------------------

def cmd_template_fill(cwd: Path, template_type: str, named: dict[str, str | None], raw: bool) -> None:
    """Create a pre-filled template file."""
    phase_num = named.get("phase")
    if not phase_num:
        error("--phase is required for template fill")

    plan_num = named.get("plan", "1")
    name = named.get("name", "")
    wave = named.get("wave", "1")

    if template_type == "plan":
        content = _fill_plan(phase_num, plan_num or "1", name, named.get("type", "execute"), wave or "1")
    elif template_type == "summary":
        content = _fill_summary(phase_num, plan_num or "1", name)
    elif template_type == "verification":
        content = _fill_verification(phase_num)
    else:
        error(f"Unknown template type: {template_type}. Available: plan, summary, verification")
        return  # unreachable, for type checker

    # Determine output path
    phase_dir = find_phase_dir(cwd, phase_num)
    if not phase_dir:
        phases_dir = opc_dir(cwd) / "phases"
        slug = generate_slug(name or f"phase-{phase_num}")
        phase_dir = phases_dir / f"{phase_num.zfill(2)}-{slug}"
        phase_dir.mkdir(parents=True, exist_ok=True)

    if template_type == "plan":
        filename = f"{plan_num.zfill(2)}-PLAN.md" if plan_num != "1" else "01-PLAN.md"
    elif template_type == "summary":
        filename = f"{plan_num.zfill(2)}-SUMMARY.md" if plan_num != "1" else "01-SUMMARY.md"
    else:
        filename = "VERIFICATION.md"

    out_path = phase_dir / filename
    out_path.write_text(content, encoding="utf-8")

    output({
        "created": True,
        "path": to_posix(out_path.relative_to(cwd)),
        "template_type": template_type,
        "phase": phase_num,
    }, raw, to_posix(out_path.relative_to(cwd)))


def cmd_template_select(cwd: Path, project_type: str | None, raw: bool) -> None:
    """List available project templates."""
    templates_dir = Path(__file__).resolve().parent.parent.parent / "templates" / "projects"
    templates: list[dict[str, str]] = []
    if templates_dir.exists():
        for d in sorted(templates_dir.iterdir()):
            if d.is_dir():
                readme = d / "README.md"
                desc = safe_read(readme).split("\n")[0] if readme.exists() else d.name
                templates.append({"name": d.name, "description": desc, "path": to_posix(d)})

    output({"templates": templates, "count": len(templates)}, raw, "\n".join(t["name"] for t in templates))


# ---------------------------------------------------------------------------
# Template generators
# ---------------------------------------------------------------------------

def _fill_plan(phase: str, plan: str, name: str, plan_type: str, wave: str) -> str:
    """Generate a pre-filled PLAN.md."""
    return f"""---
phase: {phase}
plan: {plan}
type: {plan_type}
wave: {wave}
status: pending
created: {now_iso()}
---

# Phase {phase} · Plan {plan}: {name or 'TBD'}

## Goal

**Goal:** 描述本计划的具体目标。

## Tasks

- [ ] Task 1: 描述任务
- [ ] Task 2: 描述任务
- [ ] Task 3: 描述任务

## Acceptance Criteria

1. 验收标准 1
2. 验收标准 2

## Must-Haves

### Artifacts
- `path/to/file.ext` — 描述

### Key Links
- 相关文件/API/文档链接

## Notes

实施过程中的备注。
"""


def _fill_summary(phase: str, plan: str, name: str) -> str:
    """Generate a pre-filled SUMMARY.md."""
    return f"""---
phase: {phase}
plan: {plan}
status: complete
completed: {now_iso()}
---

# Phase {phase} · Plan {plan} Summary: {name or 'TBD'}

## What Was Done

描述完成的工作。

## Files Created/Modified

| File | Action | Description |
|------|--------|-------------|
| `path/to/file.ext` | Created | 描述 |

## Commits

- `abc1234` — 提交描述

## Self-Check

- [ ] 所有任务完成
- [ ] 代码已测试
- [ ] 文档已更新

## Lessons Learned

实施过程中学到的经验。
"""


def _fill_verification(phase: str) -> str:
    """Generate a pre-filled VERIFICATION.md."""
    return f"""---
phase: {phase}
status: pending
verified: null
---

# Phase {phase} Verification

## Checklist

- [ ] 所有计划都有对应的 SUMMARY.md
- [ ] 所有任务在 SUMMARY 中标记为完成
- [ ] 文件引用全部有效
- [ ] 提交哈希在 git 历史中存在
- [ ] 无回归问题

## Test Results

| Test | Status | Notes |
|------|--------|-------|
| 单元测试 | ⬜ | |
| 集成测试 | ⬜ | |
| E2E 测试 | ⬜ | |

## Verdict

**Status:** pending

**Verifier Notes:**

"""
