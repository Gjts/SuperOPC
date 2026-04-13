#!/usr/bin/env python3
"""
instinct_generator.py — Observation-to-Rule pipeline for SuperOPC v2.

Closes the learning loop that was previously broken:
  observe.py (hook) → learning_store.detect_patterns() → THIS MODULE → .md rules

This module reads accumulated observations, detects recurring behavioral
patterns, and generates personalized rule files under rules/personal/.
These rules are then auto-loaded by the context_assembler into every session,
making the AI progressively adapt to the developer's working style.

Pipeline:
  1. Read observations from ~/.opc/learnings/observations.jsonl
  2. Detect patterns (delegate to learning_store.detect_patterns)
  3. Classify patterns into instinct categories
  4. Generate or update rules/personal/*.md
  5. Emit events for audit trail
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from event_bus import EventBus, get_event_bus
from learning_store import LearningStore


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Instinct:
    id: str
    category: str
    title: str
    description: str
    evidence: str
    strength: float
    rule_content: str


INSTINCT_CATEGORIES = {
    "workflow": "工作流偏好",
    "tooling": "工具使用习惯",
    "testing": "测试行为模式",
    "architecture": "架构决策倾向",
    "debugging": "调试策略",
    "collaboration": "协作与沟通",
}

TOOL_ACTION_TO_CATEGORY = {
    "edit-test": "testing",
    "edit-code": "workflow",
    "python-exec": "tooling",
    "dotnet-exec": "tooling",
    "git-commit": "workflow",
    "git-branch": "workflow",
    "git-diff": "debugging",
    "git-log": "debugging",
    "git-stash": "workflow",
    "search": "debugging",
    "read-file": "architecture",
    "write-file": "workflow",
    "subagent": "collaboration",
    "package-manager": "tooling",
    "shell": "tooling",
}


class InstinctGenerator:
    """Converts raw observations into personalized rule files."""

    def __init__(
        self,
        *,
        repo_root: Path | None = None,
        store: LearningStore | None = None,
        bus: EventBus | None = None,
    ):
        self._repo_root = repo_root or Path.cwd()
        self._rules_dir = self._repo_root / "rules" / "personal"
        self._store = store or LearningStore()
        self._bus = bus or get_event_bus()

    def run(self, *, min_occurrences: int = 5, dry_run: bool = False) -> list[Instinct]:
        raw_patterns = self._store.detect_patterns(min_occurrences=min_occurrences)
        if not raw_patterns:
            return []

        obs_stats = self._compute_observation_stats()
        instincts = self._classify_patterns(raw_patterns, obs_stats)

        if not instincts:
            return []

        if not dry_run:
            self._generate_rule_files(instincts)
            self._generate_index(instincts)
            self._store.evolve_instincts()
            self._bus.publish(
                "learning.instincts_generated",
                {
                    "count": len(instincts),
                    "categories": list({i.category for i in instincts}),
                    "rules_dir": str(self._rules_dir),
                },
                source="instinct_generator",
            )

        return instincts

    def _compute_observation_stats(self) -> dict[str, Any]:
        obs_file = self._store._dir / "observations.jsonl"
        if not obs_file.exists():
            return {"total": 0, "actions": {}, "tools": {}, "projects": {}, "time_distribution": {}}

        actions: Counter[str] = Counter()
        tools: Counter[str] = Counter()
        projects: Counter[str] = Counter()
        hours: Counter[int] = Counter()
        sequences: list[str] = []

        for line in obs_file.read_text(encoding="utf-8").strip().splitlines():
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            action = rec.get("action", "")
            tool = rec.get("tool", "")
            project = rec.get("project", "")
            ts_str = rec.get("ts", "")

            if action:
                actions[action] += 1
                sequences.append(action)
            if tool:
                tools[tool] += 1
            if project:
                projects[project] += 1
            if ts_str:
                try:
                    h = datetime.fromisoformat(ts_str.replace("Z", "+00:00")).hour
                    hours[h] += 1
                except ValueError:
                    pass

        tdd_ratio = 0.0
        test_edits = actions.get("edit-test", 0)
        code_edits = actions.get("edit-code", 0)
        if code_edits > 0:
            tdd_ratio = test_edits / code_edits

        return {
            "total": sum(actions.values()),
            "actions": dict(actions.most_common(20)),
            "tools": dict(tools.most_common(10)),
            "projects": dict(projects.most_common(5)),
            "time_distribution": dict(sorted(hours.items())),
            "tdd_ratio": round(tdd_ratio, 2),
            "action_sequences": sequences[-200:],
        }

    def _classify_patterns(
        self, patterns: list[dict[str, Any]], stats: dict[str, Any]
    ) -> list[Instinct]:
        instincts: list[Instinct] = []
        seen_ids: set[str] = set()

        for p in patterns:
            action = p.get("action", "")
            tool = p.get("tool", "")
            count = p.get("count", 0)
            strength = p.get("strength", 0.0)

            category = TOOL_ACTION_TO_CATEGORY.get(action, "workflow")
            instinct_id = f"{category}-{tool}-{action}".replace(" ", "-").lower()

            if instinct_id in seen_ids:
                continue
            seen_ids.add(instinct_id)

            title, description, rule_content = self._synthesize_instinct(
                category, tool, action, count, strength, stats
            )

            if not rule_content:
                continue

            instincts.append(Instinct(
                id=instinct_id,
                category=category,
                title=title,
                description=description,
                evidence=f"{count} occurrences of {tool}:{action}",
                strength=strength,
                rule_content=rule_content,
            ))

        tdd_ratio = stats.get("tdd_ratio", 0.0)
        total = stats.get("total", 0)
        if total >= 20 and "testing-tdd-ratio" not in seen_ids:
            if tdd_ratio > 0.5:
                instincts.append(Instinct(
                    id="testing-tdd-ratio",
                    category="testing",
                    title="TDD 偏好检测",
                    description=f"测试编辑与代码编辑比率 {tdd_ratio:.0%}，表明开发者偏好测试先行。",
                    evidence=f"test-edits/code-edits = {tdd_ratio:.2f}",
                    strength=min(1.0, tdd_ratio),
                    rule_content=self._tdd_strong_rule(tdd_ratio),
                ))
            elif tdd_ratio < 0.1 and total > 50:
                instincts.append(Instinct(
                    id="testing-tdd-ratio",
                    category="testing",
                    title="测试不足警告",
                    description=f"测试编辑与代码编辑比率仅 {tdd_ratio:.0%}，建议加强 TDD。",
                    evidence=f"test-edits/code-edits = {tdd_ratio:.2f}",
                    strength=0.8,
                    rule_content=self._tdd_weak_rule(tdd_ratio),
                ))

        return sorted(instincts, key=lambda i: i.strength, reverse=True)

    def _synthesize_instinct(
        self, category: str, tool: str, action: str, count: int, strength: float,
        stats: dict[str, Any],
    ) -> tuple[str, str, str]:
        if action == "edit-test" and count >= 10:
            return (
                "测试驱动习惯",
                f"检测到 {count} 次测试编辑行为，开发者偏好频繁修改测试。",
                self._rule_testing_habit(count),
            )
        if action == "edit-code" and count >= 20:
            return (
                "高频代码编辑",
                f"检测到 {count} 次代码编辑。",
                self._rule_editing_habit(count, stats),
            )
        if action == "search" and count >= 15:
            return (
                "搜索先行风格",
                f"检测到 {count} 次搜索操作，开发者偏好先搜索再行动。",
                self._rule_search_first(count),
            )
        if action == "subagent" and count >= 5:
            return (
                "子代理委派偏好",
                f"检测到 {count} 次子代理调用，开发者善于任务委派。",
                self._rule_delegation(count),
            )
        if action.startswith("git-") and count >= 10:
            return (
                f"Git {action.replace('git-', '')} 高频使用",
                f"检测到 {count} 次 {action} 操作。",
                self._rule_git_habit(action, count),
            )
        if action == "shell" and count >= 15:
            return (
                "终端重度用户",
                f"检测到 {count} 次 shell 命令执行。",
                self._rule_shell_power_user(count),
            )
        if action in ("python-exec", "dotnet-exec") and count >= 10:
            stack = "Python" if "python" in action else ".NET"
            return (
                f"{stack} 主力栈",
                f"检测到 {count} 次 {stack} 执行，确认为主力技术栈。",
                self._rule_primary_stack(stack, count),
            )
        return ("", "", "")

    @staticmethod
    def _rule_testing_habit(count: int) -> str:
        return f"""- 开发者有强烈的测试编辑习惯（{count} 次检测），在修改代码前优先考虑测试覆盖
- 建议：提交前自动检查测试覆盖率变化，覆盖率下降时发出警告
- 在规划任务时，为每个功能任务自动预留测试编写时间"""

    @staticmethod
    def _rule_editing_habit(count: int, stats: dict[str, Any]) -> str:
        tdd = stats.get("tdd_ratio", 0)
        line = f"- 高频代码编辑用户（{count} 次检测）"
        if tdd > 0.3:
            line += f"，测试比率 {tdd:.0%}，保持良好的 TDD 节奏"
        else:
            line += "，建议在每次编辑后检查是否有对应测试覆盖"
        return line

    @staticmethod
    def _rule_search_first(count: int) -> str:
        return f"""- 开发者偏好「搜索先行」风格（{count} 次检测），在行动前先搜索理解上下文
- 建议：在开始任何代码修改前，先用 Grep/Glob 搜索相关代码，确认影响范围
- 对于不熟悉的模块，优先使用 SemanticSearch 而非直接阅读"""

    @staticmethod
    def _rule_delegation(count: int) -> str:
        return f"""- 开发者善于使用子代理委派（{count} 次检测），倾向于任务分解和并行执行
- 建议：对于可拆分的任务，主动提议使用子代理并行处理
- 在计划阶段标注哪些任务适合子代理独立执行"""

    @staticmethod
    def _rule_git_habit(action: str, count: int) -> str:
        op = action.replace("git-", "")
        return f"""- 开发者频繁使用 git {op}（{count} 次检测）
- 建议：在相关操作后自动展示 git {op} 结果，减少手动查询"""

    @staticmethod
    def _rule_shell_power_user(count: int) -> str:
        return f"""- 终端重度用户（{count} 次 shell 命令），熟悉命令行操作
- 建议：可以直接提供命令行解决方案，不需要过度解释基础 shell 操作
- 优先使用 CLI 工具而非 GUI 方案"""

    @staticmethod
    def _rule_primary_stack(stack: str, count: int) -> str:
        return f"""- 主力技术栈确认：{stack}（{count} 次执行检测）
- 建议：代码示例和模板优先使用 {stack} 生态工具
- 依赖建议和最佳实践优先覆盖 {stack} 生态"""

    @staticmethod
    def _tdd_strong_rule(ratio: float) -> str:
        return f"""- 开发者展现强 TDD 偏好（测试/代码编辑比 {ratio:.0%}）
- 强化：在实现任何新功能前，必须先写失败测试，严格执行 RED-GREEN-REFACTOR
- 代码审查时优先检查测试质量和覆盖率"""

    @staticmethod
    def _tdd_weak_rule(ratio: float) -> str:
        return f"""- ⚠️ 测试覆盖不足警告（测试/代码编辑比仅 {ratio:.0%}）
- 行动：每次代码编辑后提醒编写对应测试
- 在任务规划中强制包含测试任务，不允许跳过"""

    def _generate_rule_files(self, instincts: list[Instinct]) -> None:
        self._rules_dir.mkdir(parents=True, exist_ok=True)

        by_category: dict[str, list[Instinct]] = {}
        for inst in instincts:
            by_category.setdefault(inst.category, []).append(inst)

        for category, items in by_category.items():
            cat_label = INSTINCT_CATEGORIES.get(category, category)
            filepath = self._rules_dir / f"{category}.md"

            lines = [
                f"# 个人化规则：{cat_label}",
                "",
                f"> 自动生成于 {_now()} | 基于开发者行为观察 | 请勿手动编辑",
                "",
            ]

            for inst in sorted(items, key=lambda x: x.strength, reverse=True):
                lines.append(f"## {inst.title}（置信度 {inst.strength:.0%}）")
                lines.append("")
                lines.append(inst.rule_content)
                lines.append("")

            filepath.write_text("\n".join(lines), encoding="utf-8")

    def _generate_index(self, instincts: list[Instinct]) -> None:
        index = {
            "generated_at": _now(),
            "total_instincts": len(instincts),
            "categories": {},
        }
        for inst in instincts:
            cat = inst.category
            if cat not in index["categories"]:
                index["categories"][cat] = {"count": 0, "instincts": []}
            index["categories"][cat]["count"] += 1
            index["categories"][cat]["instincts"].append({
                "id": inst.id,
                "title": inst.title,
                "strength": inst.strength,
                "evidence": inst.evidence,
            })
        index_path = self._rules_dir / "instinct-index.json"
        index_path.write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SuperOPC Instinct Generator")
    parser.add_argument("--repo", default=".", help="Repository root path")
    parser.add_argument("--min-occurrences", type=int, default=5, help="Minimum pattern occurrences")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing files")
    args = parser.parse_args()

    repo = Path(args.repo).resolve()
    generator = InstinctGenerator(repo_root=repo)
    instincts = generator.run(min_occurrences=args.min_occurrences, dry_run=args.dry_run)

    if instincts:
        print(f"Generated {len(instincts)} instincts:")
        for inst in instincts:
            print(f"  [{inst.strength:.0%}] {inst.title} ({inst.category})")
            print(f"        {inst.evidence}")
        if args.dry_run:
            print("\n(dry-run mode — no files written)")
    else:
        print("No patterns detected. Need more observation data (run more sessions).")


if __name__ == "__main__":
    main()
