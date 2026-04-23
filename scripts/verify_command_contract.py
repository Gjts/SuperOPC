#!/usr/bin/env python3
"""Verify that every slash command obeys the skill-first / agent-workflow contract.

契约（AGENTS.md v1.4.2）：
  - 白名单 local-runtime CLI 命令允许直接调用 `python scripts/<x>.py`
    或 `bin/opc-tools`
  - 其他所有命令 **必须** 在命令体里派发到 dispatcher skill
    （即出现 "调用 `<skill-id>` skill" 或等价英文文字）

Exit codes:
  0  all commands pass
  1  one or more contract violations
  2  internal error (broken frontmatter, missing files, etc.)

Usage:
    python scripts/verify_command_contract.py          # verify
    python scripts/verify_command_contract.py --json   # machine-readable
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
COMMANDS_DIR = REPO_ROOT / "commands" / "opc"
SKILLS_REGISTRY = REPO_ROOT / "skills" / "registry.json"
MAX_COMMAND_LINES = 15

# ---------------------------------------------------------------------------
# White-list for local-runtime / mixed CLI commands (AGENTS.md v1.4.2, two tiers)
# ---------------------------------------------------------------------------
# Tier 1: LOCAL_RUNTIME_WHITELIST (6) — low-friction local runtime entrypoints.
#   Some are pure read-only, while others document tightly scoped local writes
#   such as safe repair, local profile recording, or research artifact output.
#   Command docs must declare those guarded write paths explicitly.
#
# Tier 2: MIXED_LOW_FRICTION_WHITELIST (3) — list/query mode is read-only,
#   create mode writes ONE lightweight markdown entry under .opc/<dir>/.
#   Command doc MUST carry `<!-- MIXED: ... -->` HTML comment in its ## 动作
#   section so this lint can verify the contract is declared, not implicit.

LOCAL_RUNTIME_WHITELIST: set[str] = {
    "opc-health",      # scripts/opc_health.py — 诊断默认只读；--repair 受控修复
    "opc-dashboard",   # scripts/opc_dashboard.py — 纯只读汇总
    "opc-stats",       # scripts/opc_stats.py — 纯只读计数
    "opc-intel",       # bin/opc-tools intel — 查询本地 runtime；refresh 走 agent
    "opc-profile",     # bin/opc-tools profile — 本地 profile 读写（不写项目 .opc/）
    "opc-research",    # bin/opc-tools research — feed/run 受控写研究产物
}

MIXED_LOW_FRICTION_WHITELIST: set[str] = {
    "opc-thread",      # scripts/opc_thread.py — list readonly, create writes .opc/threads/
    "opc-seed",        # scripts/opc_seed.py — list readonly, create writes .opc/seeds/
    "opc-backlog",     # scripts/opc_backlog.py — list readonly, create writes .opc/todos/
}

# Union for convenience; use the specific tier when checking contracts.
READ_ONLY_CLI_WHITELIST: set[str] = LOCAL_RUNTIME_WHITELIST | MIXED_LOW_FRICTION_WHITELIST

_MIXED_MARKER_PATTERN = re.compile(
    r"<!--\s*MIXED:\s*list\s*=\s*readonly\s*,\s*create\s*=\s*writes\s+\S+\s*-->",
    re.IGNORECASE,
)
_INTEL_REFRESH_PATTERN = re.compile(r"\brefresh\b", re.IGNORECASE)
_INTEL_REFRESH_RUNTIME_PATTERN = re.compile(
    r"^.*refresh.*`(?:python(?:\s+-m)?|py|uv\s+run)\s+bin/opc-tools\s+intel\b.*$",
    re.IGNORECASE | re.MULTILINE,
)
_INTEL_REFRESH_ENGINE_PATTERN = re.compile(
    r"^.*refresh.*(?:scripts/engine/intel_engine\.py|重建\s+`.opc/intel/`).*$",
    re.IGNORECASE | re.MULTILINE,
)
_HEALTH_REPAIR_PATTERN = re.compile(r"--repair|\brepair\b", re.IGNORECASE)
_PROFILE_RECORD_PATTERN = re.compile(r"\brecord\b", re.IGNORECASE)
_RESEARCH_FEED_RUN_PATTERN = re.compile(r"\bfeed\b.*\brun\b|\brun\b.*\bfeed\b", re.IGNORECASE | re.DOTALL)


@dataclass
class Violation:
    command: str
    path: str
    issue: str
    hint: str = ""


@dataclass
class Report:
    commands_checked: int = 0
    local_runtime: int = 0
    mixed_low_friction: int = 0
    dispatchers: int = 0
    violations: list[Violation] = field(default_factory=list)

    @property
    def pure_readonly(self) -> int:
        """Compatibility alias for older JSON/tests that still expect the old field name."""
        return self.local_runtime

    @property
    def whitelisted(self) -> int:
        return self.local_runtime + self.mixed_low_friction

    def as_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["pure_readonly"] = self.pure_readonly
        d["whitelisted"] = self.whitelisted
        return d


def _parse_frontmatter(md_path: Path) -> tuple[dict[str, Any], str]:
    text = md_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"{md_path}: missing YAML frontmatter delimited by ---")
    fm = yaml.safe_load(parts[1]) or {}
    if not isinstance(fm, dict):
        raise ValueError(f"{md_path}: frontmatter is not a mapping")
    return fm, parts[2]


def _load_dispatcher_skill_ids() -> set[str]:
    if not SKILLS_REGISTRY.exists():
        return set()
    data = json.loads(SKILLS_REGISTRY.read_text(encoding="utf-8"))
    return {
        s["id"]
        for s in data.get("skills", [])
        if s.get("type") == "dispatcher" and s.get("id")
    }


_SKILL_CALL_PATTERNS = [
    # 中文: 调用 `<id>` skill / 调用 <id> skill
    re.compile(r"调用\s*[`\"']?([a-z][a-z0-9-]+)[`\"']?\s*skill", re.IGNORECASE),
    # English: dispatches <id> skill / invoke <id> skill / use <id> skill
    re.compile(
        r"(?:dispatch(?:es)?|invoke|use|calls?)\s+(?:the\s+)?[`\"']?([a-z][a-z0-9-]+)[`\"']?\s+skill",
        re.IGNORECASE,
    ),
]


def _extract_skill_references(body: str) -> set[str]:
    hits: set[str] = set()
    for pat in _SKILL_CALL_PATTERNS:
        for m in pat.finditer(body):
            hits.add(m.group(1).lower())
    return hits


_DIRECT_LOCAL_RUNTIME_PATTERN = re.compile(
    r"`(?:python(?:\s+-m)?|py|uv\s+run)\s+(?:[\w/\\.-]+\.py\b|(?:[\w./\\-]+[\\/])?bin[\\/]+opc-tools\b)",
    re.IGNORECASE,
)


def _mentions_direct_local_runtime_call(body: str) -> bool:
    return bool(_DIRECT_LOCAL_RUNTIME_PATTERN.search(body))


def _line_count(md_path: Path) -> int:
    return len(md_path.read_text(encoding="utf-8").splitlines())


def _verify_guarded_local_runtime_command(
    *,
    name: str,
    body: str,
    rel: str,
    dispatcher_ids: set[str],
) -> list[Violation]:
    violations: list[Violation] = []

    if name == "opc-health" and not _HEALTH_REPAIR_PATTERN.search(body):
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="local runtime command missing explicit `--repair` contract",
                hint="Document that diagnostics are local-runtime safe and `--repair` performs a guarded local fix.",
            )
        )

    if name == "opc-profile" and not _PROFILE_RECORD_PATTERN.search(body):
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="local runtime command missing explicit `record` write-mode contract",
                hint="Mention `record` in the command doc so the local-profile write path stays visible at the command layer.",
            )
        )

    if name == "opc-research" and not _RESEARCH_FEED_RUN_PATTERN.search(body):
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="local runtime command missing explicit `feed` / `run` artifact-write contract",
                hint="Document that `methods` / `insights` are consumable locally while `feed` / `run` write research artifacts under `.opc/`.",
            )
        )

    if name != "opc-intel":
        return violations

    refs = _extract_skill_references(body)
    dispatched = refs & dispatcher_ids

    if not _INTEL_REFRESH_PATTERN.search(body):
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="local runtime command missing explicit refresh contract",
                hint="Document `refresh` explicitly so the command contract can verify it routes through a dispatcher skill.",
            )
        )
        return violations

    if "workflow-modes" not in dispatched:
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="`/opc-intel refresh` must dispatch `workflow-modes` skill",
                hint="Keep read-only subcommands on the local runtime, but route `refresh` through `workflow-modes` so it can delegate to `opc-intel-updater`.",
            )
        )

    if _INTEL_REFRESH_RUNTIME_PATTERN.search(body):
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="`/opc-intel refresh` must not be documented as a direct local runtime call",
                hint="Scope `python bin/opc-tools intel ...` to query/status/validate/snapshot/diff only, and give `refresh` its own dispatcher line.",
            )
        )

    if _INTEL_REFRESH_ENGINE_PATTERN.search(body):
        violations.append(
            Violation(
                command=name,
                path=rel,
                issue="`/opc-intel refresh` must not bypass the dispatcher with a direct engine rebuild note",
                hint="Describe the agent path (`workflow-modes` -> `opc-intel-updater`) instead of saying refresh rebuilds `.opc/intel/` directly.",
            )
        )

    return violations


def verify() -> Report:
    report = Report()
    if not COMMANDS_DIR.exists():
        raise RuntimeError(f"commands dir not found: {COMMANDS_DIR}")

    dispatcher_ids = _load_dispatcher_skill_ids()
    if not dispatcher_ids:
        raise RuntimeError(
            f"skills/registry.json missing or no dispatcher skills found: {SKILLS_REGISTRY}"
        )

    md_files = sorted(COMMANDS_DIR.glob("*.md"))
    for md in md_files:
        rel = str(md.relative_to(REPO_ROOT)).replace("\\", "/")
        report.commands_checked += 1
        line_count = _line_count(md)

        if line_count > MAX_COMMAND_LINES:
            report.violations.append(
                Violation(
                    command=md.stem,
                    path=rel,
                    issue=f"command exceeds {MAX_COMMAND_LINES}-line entry budget ({line_count} lines)",
                    hint=(
                        "Keep command files as thin entrypoints: frontmatter + dispatch line + "
                        "minimal parameter note. Move workflow detail to dispatcher skills, agents, "
                        "or references."
                    ),
                )
            )

        try:
            fm, body = _parse_frontmatter(md)
        except Exception as exc:
            report.violations.append(
                Violation(
                    command=md.stem,
                    path=rel,
                    issue=str(exc),
                    hint="Command file must start with YAML frontmatter (--- ... ---).",
                )
            )
            continue

        name = fm.get("name") or md.stem
        if not fm.get("name"):
            report.violations.append(
                Violation(
                    command=name,
                    path=rel,
                    issue="frontmatter missing 'name' field",
                    hint="Add 'name: <command-id>' to YAML frontmatter.",
                )
            )

        if name in LOCAL_RUNTIME_WHITELIST:
            report.local_runtime += 1
            report.violations.extend(
                _verify_guarded_local_runtime_command(
                    name=name,
                    body=body,
                    rel=rel,
                    dispatcher_ids=dispatcher_ids,
                )
            )
            continue

        if name in MIXED_LOW_FRICTION_WHITELIST:
            report.mixed_low_friction += 1
            # MIXED 命令必须携带 <!-- MIXED: ... --> 注释，让契约在命令层显式可读
            if not _MIXED_MARKER_PATTERN.search(body):
                report.violations.append(
                    Violation(
                        command=name,
                        path=rel,
                        issue="MIXED whitelist command missing <!-- MIXED: ... --> marker in ## 动作",
                        hint=(
                            "Add a single HTML comment on its own line inside ## 动作, e.g. "
                            "'<!-- MIXED: list=readonly, create=writes .opc/threads/ -->'. "
                            "This makes the read/write bifurcation machine-checkable per AGENTS.md §档二."
                        ),
                    )
                )
            continue

        # Non-whitelist command: must dispatch a skill.
        refs = _extract_skill_references(body)
        dispatched = refs & dispatcher_ids
        has_direct_script = _mentions_direct_local_runtime_call(body)

        if not dispatched:
            report.violations.append(
                Violation(
                    command=name,
                    path=rel,
                    issue="command does not dispatch any dispatcher skill in its body",
                    hint=(
                        "Add a line like: 调用 `<skill-id>` skill. "
                        f"Available dispatchers: {sorted(dispatcher_ids)}. "
                        f"If this is a direct local-runtime / mixed CLI, add '{name}' to the "
                        "direct-call whitelist in scripts/verify_command_contract.py."
                    ),
                )
            )
            continue

        report.dispatchers += 1

        if has_direct_script:
            report.violations.append(
                Violation(
                    command=name,
                    path=rel,
                    issue="command body contains a direct local runtime invocation",
                    hint=(
                        "Commands must route through the skill; any direct `python scripts/...` "
                        "or `python bin/opc-tools ...` call must happen inside the agent workflow, "
                        "not the command file. Remove the local runtime invocation and let the "
                        "dispatched skill/agent call it."
                    ),
                )
            )

    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    try:
        report = verify()
    except Exception as exc:
        print(f"internal error: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(report.as_dict(), ensure_ascii=False, indent=2))
    else:
        print(
            f"# command contract verification\n"
            f"  commands checked      : {report.commands_checked}\n"
            f"  whitelist local RT    : {report.local_runtime}\n"
            f"  whitelist mixed (RW)  : {report.mixed_low_friction}\n"
            f"  dispatchers           : {report.dispatchers}\n"
            f"  violations            : {len(report.violations)}"
        )
        if report.violations:
            print("\n# violations")
            for v in report.violations:
                print(f"- [{v.command}] {v.path}")
                print(f"    issue: {v.issue}")
                if v.hint:
                    print(f"    hint : {v.hint}")

    return 1 if report.violations else 0


if __name__ == "__main__":
    raise SystemExit(main())
