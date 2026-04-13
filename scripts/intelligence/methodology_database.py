#!/usr/bin/env python3
"""
methodology_database.py — Expert methodology database for SuperOPC.

Inspired by skill-from-masters.  Provides a queryable store of proven
expert methodologies that can be injected into planning, brainstorming,
and decision-making contexts.

Pre-loaded methodologies cover:
  - Business validation (Mom Test, Lean Startup)
  - Communication (Minto Pyramid, SCQA)
  - Product design (Jobs-to-be-Done, Design Sprint)
  - Pricing (Van Westendorp, Gabor-Granger)
  - Growth (AARRR, ICE scoring)
  - Engineering (TDD, ADR, C4 Model)

Users can add custom methodologies via the CLI or programmatically.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DB_DIR = REPO_ROOT / ".opc" / "intelligence" / "methodologies"


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class Methodology:
    id: str
    name: str
    author: str
    domain: str
    one_liner: str
    core_principles: list[str]
    steps: list[str]
    when_to_use: list[str]
    common_mistakes: list[str]
    anchor_quotes: list[str] = field(default_factory=list)
    source: str = ""
    tags: list[str] = field(default_factory=list)
    added_at: str = field(default_factory=_now)


BUILTIN_METHODOLOGIES: list[Methodology] = [
    Methodology(
        id="mom-test",
        name="The Mom Test",
        author="Rob Fitzpatrick",
        domain="validation",
        one_liner="用户访谈的黄金法则：谈他们的生活，而不是你的想法。",
        core_principles=[
            "不要告诉用户你的想法，问他们的生活",
            "问具体的过去经历，而不是假设性问题",
            "少说多听，让用户讲述真实故事",
            "坏消息是好消息，因为它帮你避免浪费",
            "承诺和推进比赞美更有价值",
        ],
        steps=[
            "准备 3 个你最想验证的假设",
            "找到 5-10 个潜在用户（不是朋友和家人）",
            "用开放式问题开始：'告诉我你上次遇到 X 问题的经历'",
            "追问具体细节：'你当时怎么解决的？花了多少时间/钱？'",
            "寻找承诺信号：'如果有这样的工具，你愿意付多少？现在就试用？'",
            "汇总发现，更新假设，决定是否继续",
        ],
        when_to_use=[
            "产品想法验证阶段",
            "不确定用户是否真的有这个痛点",
            "需要判断是否值得投入开发",
        ],
        common_mistakes=[
            "问 '你觉得这个想法怎么样？'（引导性问题）",
            "只和朋友聊（他们会为了你的感受撒谎）",
            "听到赞美就以为验证通过（赞美没有价值）",
            "忘记追问具体行为和金额",
        ],
        anchor_quotes=[
            "Opinions are worthless.",
            "Talk about their life, not your idea.",
            "Compliments are the currency of polite conversation, not of truth.",
        ],
        source="Rob Fitzpatrick《The Mom Test》",
        tags=["validation", "user-interview", "lean"],
    ),
    Methodology(
        id="minto-pyramid",
        name="Minto Pyramid Principle",
        author="Barbara Minto",
        domain="communication",
        one_liner="先说结论，再给论据，用金字塔结构组织思维。",
        core_principles=[
            "结论先行：先给出答案/建议，再展开论证",
            "MECE 原则：论据必须互相独立、完全穷尽",
            "归纳分组：相似观点归为一组，每组 3-5 个要点",
            "逻辑递进：论据之间有内在逻辑顺序",
        ],
        steps=[
            "确定你的核心结论（一句话能说清楚）",
            "列出支撑结论的 2-4 个关键论据",
            "为每个论据准备子论据或数据支撑",
            "检查 MECE：论据之间是否有重叠？是否遗漏了重要方面？",
            "用 SCQA 开场：情境(S) → 冲突(C) → 问题(Q) → 答案(A)",
        ],
        when_to_use=[
            "写商业邮件、报告、提案",
            "向投资人/客户做演示",
            "产品文档和技术方案的结构化",
            "团队沟通需要简洁有力的场合",
        ],
        common_mistakes=[
            "铺垫太长，读者等不到结论",
            "论据之间有重叠（违反 MECE）",
            "用时间顺序代替逻辑结构",
            "结论太抽象，不够具体和可行动",
        ],
        anchor_quotes=[
            "Always present the answer before the argument.",
            "Ideas at any level must be summaries of the ideas below.",
        ],
        source="Barbara Minto《The Minto Pyramid Principle》",
        tags=["communication", "writing", "structure"],
    ),
    Methodology(
        id="lean-startup",
        name="Lean Startup",
        author="Eric Ries",
        domain="validation",
        one_liner="构建-测量-学习循环，用最小可行产品验证假设。",
        core_principles=[
            "构建-测量-学习（Build-Measure-Learn）循环",
            "最小可行产品（MVP）：用最少资源验证核心假设",
            "经验证的学习（Validated Learning）：用数据而非直觉做决策",
            "转向或坚持（Pivot or Persevere）：有纪律地决定方向",
            "创新会计（Innovation Accounting）：衡量进步而非虚荣指标",
        ],
        steps=[
            "明确你的关键假设（价值假设 + 增长假设）",
            "构建最小可行产品（MVP）来测试假设",
            "设定成功/失败标准（不是上线后再想）",
            "发布并收集数据",
            "分析数据，决定转向还是坚持",
            "重复循环",
        ],
        when_to_use=[
            "新产品/功能的早期阶段",
            "市场不确定性高的场景",
            "资源有限，需要快速验证",
        ],
        common_mistakes=[
            "MVP 做得太大（不够 minimum）",
            "没有设定明确的成功标准",
            "用虚荣指标（注册数）代替行动指标（付费率）",
            "害怕 pivot，在失败假设上浪费时间",
        ],
        anchor_quotes=[
            "The only way to win is to learn faster than anyone else.",
            "If we do not know who the customer is, we do not know what quality is.",
        ],
        source="Eric Ries《The Lean Startup》",
        tags=["validation", "mvp", "startup", "lean"],
    ),
    Methodology(
        id="jobs-to-be-done",
        name="Jobs to be Done (JTBD)",
        author="Clayton Christensen",
        domain="product",
        one_liner="用户不是购买产品，而是雇佣产品来完成某个任务。",
        core_principles=[
            "人们'雇佣'产品来完成特定的'任务'",
            "任务 = 功能需求 + 情感需求 + 社交需求",
            "竞争对手不是类似产品，而是用户当前的替代方案",
            "创新来自发现未被满足的任务，而非改进现有产品",
        ],
        steps=[
            "观察用户当前如何完成这个任务（现状）",
            "发现任务中的痛点和摩擦（挣扎时刻）",
            "理解用户在情感和社交层面的需求",
            "设计产品来更好地完成整个任务",
            "测试用户是否会'解雇'旧方案，'雇佣'你的产品",
        ],
        when_to_use=[
            "产品定位和差异化",
            "理解为什么用户选择（或不选择）你的产品",
            "发现新的市场机会",
        ],
        common_mistakes=[
            "只关注功能需求，忽略情感和社交需求",
            "把竞品定义为同类产品（实际上可能是 Excel 或便签纸）",
            "问用户想要什么功能（而不是他们要完成什么任务）",
        ],
        anchor_quotes=[
            "People don't want a quarter-inch drill. They want a quarter-inch hole.",
            "Customers don't buy products; they hire them to do a job.",
        ],
        source="Clayton Christensen《Competing Against Luck》",
        tags=["product", "innovation", "user-research"],
    ),
    Methodology(
        id="design-sprint",
        name="Design Sprint",
        author="Jake Knapp (Google Ventures)",
        domain="product",
        one_liner="5 天内从问题到测试过的原型。",
        core_principles=[
            "时间压力激发创造力",
            "原型胜过辩论",
            "真实用户的反馈胜过专家意见",
            "聚焦一个大问题，不要试图解决所有问题",
        ],
        steps=[
            "周一：理解问题，选择目标",
            "周二：草拟方案，每人独立设计",
            "周三：决策，选择最佳方案",
            "周四：制作逼真原型",
            "周五：用 5 个真实用户测试",
        ],
        when_to_use=[
            "新产品方向不确定，需要快速验证",
            "团队对方案有分歧",
            "一人公司可以压缩为 2-3 天的迷你版",
        ],
        common_mistakes=[
            "试图在一次 sprint 中解决太多问题",
            "原型做得太精致（浪费时间）或太粗糙（无法测试）",
            "测试时引导用户，而不是观察",
        ],
        anchor_quotes=[
            "Don't argue. Test.",
            "The bigger the challenge, the better the sprint.",
        ],
        source="Jake Knapp《Sprint》",
        tags=["product", "design", "prototyping", "validation"],
    ),
    Methodology(
        id="aarrr-pirate-metrics",
        name="AARRR Pirate Metrics",
        author="Dave McClure",
        domain="growth",
        one_liner="用 5 个关键指标驱动增长：获客、激活、留存、收入、推荐。",
        core_principles=[
            "Acquisition（获客）：用户从哪里来？",
            "Activation（激活）：用户是否体验到核心价值？",
            "Retention（留存）：用户是否回来？",
            "Revenue（收入）：用户是否付费？",
            "Referral（推荐）：用户是否推荐给别人？",
        ],
        steps=[
            "为每个阶段定义关键指标",
            "测量当前漏斗各层转化率",
            "找到泄漏最严重的环节",
            "优先修复泄漏最大的环节",
            "设计实验来改善该环节",
            "重复测量-改善循环",
        ],
        when_to_use=[
            "产品已有用户，需要系统化增长",
            "不确定应该优先改善什么",
            "需要与团队对齐增长优先级",
        ],
        common_mistakes=[
            "同时优化所有环节（应该聚焦）",
            "用虚荣指标替代行动指标",
            "只关注获客，忽略留存",
            "没有对照组，无法判断改善是否有效",
        ],
        anchor_quotes=["Fix retention before you scale acquisition."],
        source="Dave McClure — 500 Startups",
        tags=["growth", "metrics", "funnel"],
    ),
    Methodology(
        id="ice-scoring",
        name="ICE Scoring",
        author="Sean Ellis",
        domain="growth",
        one_liner="用 Impact × Confidence × Ease 打分来优先排序增长实验。",
        core_principles=[
            "Impact（影响力）：如果成功，效果有多大？1-10",
            "Confidence（置信度）：你有多确信这会成功？1-10",
            "Ease（容易度）：实现起来有多容易？1-10",
            "总分 = I × C × E / 10，分高优先做",
        ],
        steps=[
            "列出所有待评估的增长想法",
            "每个想法打 ICE 三项分数（1-10）",
            "计算总分并排序",
            "从最高分开始执行",
            "每次只做一个实验",
            "实验结束后根据结果更新分数",
        ],
        when_to_use=[
            "有太多增长想法，需要排优先级",
            "团队对做什么有分歧",
            "资源有限，需要最大化投入产出比",
        ],
        common_mistakes=[
            "所有想法都打高分（通货膨胀）",
            "只考虑 Impact 不考虑 Ease",
            "打完分不执行",
        ],
        anchor_quotes=["The best growth idea is the one you actually test."],
        source="Sean Ellis《Hacking Growth》",
        tags=["growth", "prioritization", "experimentation"],
    ),
    Methodology(
        id="tdd-kent-beck",
        name="Test-Driven Development",
        author="Kent Beck",
        domain="engineering",
        one_liner="红-绿-重构：先写失败测试，再写最少代码通过，最后重构。",
        core_principles=[
            "不写测试就不写生产代码",
            "只写刚好让测试通过的代码",
            "重构在绿灯状态下进行",
            "小步前进，每次只处理一个行为",
        ],
        steps=[
            "🔴 RED：写一个描述期望行为的失败测试",
            "🟢 GREEN：写最少的代码让测试通过",
            "🔵 REFACTOR：在所有测试通过的状态下清理代码",
            "重复循环",
        ],
        when_to_use=[
            "所有新功能开发",
            "所有 bug 修复（先写复现测试）",
            "重构前确保行为不变",
        ],
        common_mistakes=[
            "写了代码再补测试（这不是 TDD）",
            "测试粒度太粗（一个测试覆盖太多行为）",
            "跳过 refactor 步骤",
            "测试实现细节而非行为",
        ],
        anchor_quotes=[
            "Never write a single line of code unless you have a failing automated test.",
            "Make it work, make it right, make it fast.",
        ],
        source="Kent Beck《Test-Driven Development: By Example》",
        tags=["engineering", "testing", "tdd", "quality"],
    ),
    Methodology(
        id="c4-model",
        name="C4 Model",
        author="Simon Brown",
        domain="engineering",
        one_liner="4 层架构图：系统上下文 → 容器 → 组件 → 代码。",
        core_principles=[
            "从高到低 4 层递进：Context → Container → Component → Code",
            "每层服务不同的受众和决策需求",
            "图上每个元素都必须有名称、描述和职责",
            "不是 UML，是实用的架构沟通工具",
        ],
        steps=[
            "Level 1 - System Context：画出系统与外部用户/系统的关系",
            "Level 2 - Container：拆出主要技术容器（Web App、API、DB 等）",
            "Level 3 - Component：每个容器内的逻辑组件",
            "Level 4 - Code：关键组件的代码级结构（通常只为复杂模块画）",
        ],
        when_to_use=[
            "新项目架构设计",
            "向团队/新成员解释系统结构",
            "架构决策记录（ADR）的配图",
        ],
        common_mistakes=[
            "一张图试图展示所有层级",
            "忘记标注技术选型（语言/框架/协议）",
            "把 C4 当成 UML 来画",
        ],
        anchor_quotes=["Architecture diagrams should be treated like code: kept up to date and versioned."],
        source="Simon Brown — https://c4model.com",
        tags=["engineering", "architecture", "documentation", "visualization"],
    ),
    Methodology(
        id="van-westendorp",
        name="Van Westendorp Price Sensitivity Meter",
        author="Peter Van Westendorp",
        domain="pricing",
        one_liner="用 4 个价格问题找到最优定价区间。",
        core_principles=[
            "问 4 个价格问题确定用户的价格心理区间",
            "交叉点分析得出最优价格（OPP）和可接受范围",
            "不需要大样本，20-30 个回答即可",
        ],
        steps=[
            "问用户 4 个价格问题：",
            "  1. 多少钱你觉得太便宜，质量可能有问题？",
            "  2. 多少钱你觉得很划算？",
            "  3. 多少钱你觉得开始变贵了？",
            "  4. 多少钱你觉得太贵了，绝对不会买？",
            "画出 4 条累积分布曲线",
            "找到交叉点：最优价格点（OPP）和可接受范围",
        ],
        when_to_use=[
            "新产品定价",
            "定价调整前的用户调研",
            "确认定价是否在用户心理区间内",
        ],
        common_mistakes=[
            "样本太少（建议 20+ 回答）",
            "只问目标用户以外的人",
            "忽略细分市场（不同用户群价格预期不同）",
        ],
        anchor_quotes=[],
        source="Peter Van Westendorp — Price Sensitivity Meter",
        tags=["pricing", "research", "validation"],
    ),
]


class MethodologyDatabase:
    """Queryable store of expert methodologies."""

    def __init__(self, db_dir: Path | None = None):
        self._dir = db_dir or DB_DIR
        self._index: dict[str, Methodology] = {}
        self._loaded = False

    def _ensure_loaded(self) -> None:
        if self._loaded:
            return
        for m in BUILTIN_METHODOLOGIES:
            self._index[m.id] = m

        self._dir.mkdir(parents=True, exist_ok=True)
        for fpath in self._dir.glob("*.json"):
            try:
                data = json.loads(fpath.read_text(encoding="utf-8"))
                m = self._dict_to_methodology(data)
                self._index[m.id] = m
            except (json.JSONDecodeError, OSError, TypeError):
                continue
        self._loaded = True

    def query(
        self,
        *,
        domain: str = "",
        tags: list[str] | None = None,
        keyword: str = "",
        limit: int = 10,
    ) -> list[Methodology]:
        self._ensure_loaded()
        results: list[Methodology] = []

        for m in self._index.values():
            if domain and m.domain != domain:
                continue
            if tags and not any(t in m.tags for t in tags):
                continue
            if keyword:
                kw = keyword.lower()
                searchable = f"{m.name} {m.one_liner} {m.author} {' '.join(m.tags)}".lower()
                if kw not in searchable:
                    continue
            results.append(m)

        return results[:limit]

    def get(self, methodology_id: str) -> Methodology | None:
        self._ensure_loaded()
        return self._index.get(methodology_id)

    def add(self, methodology: Methodology) -> None:
        self._ensure_loaded()
        self._index[methodology.id] = methodology
        self._persist(methodology)

    def list_domains(self) -> dict[str, int]:
        self._ensure_loaded()
        domains: dict[str, int] = {}
        for m in self._index.values():
            domains[m.domain] = domains.get(m.domain, 0) + 1
        return domains

    def get_context_injection(self, *, domain: str = "", tags: list[str] | None = None, limit: int = 3) -> list[dict[str, Any]]:
        results = self.query(domain=domain, tags=tags, limit=limit)
        return [
            {
                "name": m.name,
                "author": m.author,
                "domain": m.domain,
                "one_liner": m.one_liner,
                "steps_summary": m.steps[:3],
                "anchor_quote": m.anchor_quotes[0] if m.anchor_quotes else "",
            }
            for m in results
        ]

    def _persist(self, m: Methodology) -> None:
        self._dir.mkdir(parents=True, exist_ok=True)
        filepath = self._dir / f"{m.id}.json"
        filepath.write_text(
            json.dumps(asdict(m), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    @staticmethod
    def _dict_to_methodology(data: dict[str, Any]) -> Methodology:
        known = {f.name for f in Methodology.__dataclass_fields__.values()}
        return Methodology(**{k: v for k, v in data.items() if k in known})


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SuperOPC Expert Methodology Database")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("list", help="List all domains and methodology counts")

    q = sub.add_parser("query", help="Search methodologies")
    q.add_argument("--domain", default="", help="Filter by domain")
    q.add_argument("--keyword", default="", help="Search keyword")
    q.add_argument("--tags", default="", help="Comma-separated tags")

    show = sub.add_parser("show", help="Show a specific methodology")
    show.add_argument("id", help="Methodology ID")

    args = parser.parse_args()
    db = MethodologyDatabase()

    if args.command == "list":
        domains = db.list_domains()
        total = sum(domains.values())
        print(f"📚 {total} methodologies across {len(domains)} domains:\n")
        for domain, count in sorted(domains.items()):
            print(f"  {domain}: {count}")
            for m in db.query(domain=domain):
                print(f"    - {m.id}: {m.name} ({m.author})")

    elif args.command == "query":
        tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else None
        results = db.query(domain=args.domain, keyword=args.keyword, tags=tags)
        if results:
            for m in results:
                print(f"📖 {m.name} ({m.author}) [{m.domain}]")
                print(f"   {m.one_liner}")
                print()
        else:
            print("No methodologies found matching your criteria.")

    elif args.command == "show":
        m = db.get(args.id)
        if m:
            print(f"📖 {m.name}")
            print(f"   作者: {m.author}")
            print(f"   领域: {m.domain}")
            print(f"   一句话: {m.one_liner}\n")
            print("   核心原则:")
            for p in m.core_principles:
                print(f"     • {p}")
            print("\n   步骤:")
            for i, s in enumerate(m.steps, 1):
                print(f"     {i}. {s}")
            print("\n   何时使用:")
            for u in m.when_to_use:
                print(f"     ✅ {u}")
            print("\n   常见错误:")
            for e in m.common_mistakes:
                print(f"     ❌ {e}")
            if m.anchor_quotes:
                print("\n   金句:")
                for q in m.anchor_quotes:
                    print(f'     "{q}"')
        else:
            print(f"Methodology '{args.id}' not found.")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
