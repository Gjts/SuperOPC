#!/usr/bin/env python3
"""
opc_research.py — Market research pipeline: feed → insights → methodology → Markdown.

Writes:
  - .opc/market_feed_latest.json (via feed_scraper)
  - .opc/intelligence/insights-*.json (via insight_generator)
  - .opc/intelligence/extracted-skills/*.json (via skill_extractor)
  - .opc/research/YYYY-MM-DD-<slug>.md (+ optional .meta.json)
  - Optional mirror: docs/research/ (if --mirror-docs)
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_SCRIPT = Path(__file__).resolve().parent
for _p in (_SCRIPT, _SCRIPT / "engine", _SCRIPT / "intelligence"):
    _s = str(_p)
    if _s not in sys.path:
        sys.path.insert(0, _s)

from feed_scraper import compose_intelligence_report, feed_paths
from insight_generator import Insight, InsightGenerator
from methodology_database import MethodologyDatabase
from skill_extractor import SkillExtractor


def _slug(text: str) -> str:
    import re

    s = re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
    return (s or "research")[:60]


def _render_markdown(
    *,
    query: str,
    feed_report: dict[str, Any],
    insights: list[Insight],
    methodologies: list[dict[str, Any]],
) -> str:
    lines = [
        f"## 研究报告：{query}",
        "",
        f"**生成时间（UTC）：** {datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')}",
        f"**数据源成功：** {', '.join(feed_report.get('sources_succeeded', [])) or '无'}",
        f"**guardrail_status：** {feed_report.get('guardrail_status', '')}",
        "",
        "### 关键发现（结构化洞察）",
        "",
    ]
    for ins in insights[:12]:
        lines.append(f"- **[{ins.source}]** {ins.title} _(score {ins.relevance_score:.2f})_")
        lines.append(f"  - {ins.summary[:200]}{'…' if len(ins.summary) > 200 else ''}")
        for a in ins.action_items[:2]:
            lines.append(f"  - → {a}")
        lines.append("")

    lines.extend(["### 方法论透镜（内置库）", ""])
    if methodologies:
        for m in methodologies:
            lines.append(f"- **{m.get('name', '')}**（{m.get('domain', '')}）— {m.get('one_liner', '')}")
            steps = m.get("steps_summary") or []
            if steps:
                lines.append(f"  - 步骤摘要：{'；'.join(str(x) for x in steps[:3])}")
            if m.get("anchor_quote"):
                lines.append(f"  - _{m['anchor_quote']}_")
            lines.append("")
    else:
        lines.append("_（未匹配到方法论；可扩展 `.opc/intelligence/methodologies/`）_\n")

    lines.extend(
        [
            "### 行动建议",
            "1. 用 `opc-tools research insights --cwd <项目>` 刷新洞察 JSON。",
            "2. 将高置信发现与 `validate-idea` / `market-research` 技能结论交叉验证。",
            "3. 把未验证假设记入 PLAN 的 `opc-assumptions-analyzer` 段落。",
            "",
        ]
    )
    return "\n".join(lines)


def run_market_research(
    opc_dir: Path,
    query: str,
    *,
    days: int = 30,
    subreddit: str = "",
    sources: list[str] | None = None,
    mirror_docs: bool = True,
    extract_skills: bool = True,
    quiet: bool = False,
) -> dict[str, Any]:
    """Run scrape → insights → methodology summary → Markdown under `.opc/research/`."""
    query = query.strip()
    if not query:
        raise ValueError("query is required")

    feed_report = compose_intelligence_report(
        query,
        days=days,
        subreddit=subreddit,
        sources=sources,
        opc_dir=opc_dir,
    )
    generator = InsightGenerator(opc_dir)
    insights = generator.process_latest()

    db = MethodologyDatabase(db_dir=opc_dir / "intelligence" / "methodologies")
    tags = [w for w in query.lower().split() if len(w) > 2][:8]
    methodologies = db.get_context_injection(tags=tags if tags else None, limit=4)
    if not methodologies:
        methodologies = db.get_context_injection(limit=4)

    extracted_skills_dir = opc_dir / "intelligence" / "extracted-skills"
    extracted_skills_count = 0
    if extract_skills:
        extractor = SkillExtractor(output_dir=extracted_skills_dir, verbose=not quiet)
        extracted = extractor.search_and_extract(query, limit=3, min_stars=1000)
        extracted_skills_count = len(extracted)

    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    slug = _slug(query)
    stem = f"{date_str}-{slug}"

    research_dir = opc_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)
    md_path = research_dir / f"{stem}.md"
    body = _render_markdown(
        query=query,
        feed_report=feed_report,
        insights=insights,
        methodologies=methodologies,
    )
    md_path.write_text(body, encoding="utf-8")

    feed_dest, _ = feed_paths(opc_dir)
    meta = {
        "query": query,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "feed_path": str(feed_dest),
        "markdown_path": str(md_path),
        "sources_succeeded": feed_report.get("sources_succeeded", []),
        "guardrail_status": feed_report.get("guardrail_status"),
        "insights_count": len(insights),
        "methodologies": [m.get("name") for m in methodologies],
        "extracted_skills_dir": str(extracted_skills_dir),
        "extracted_skills_count": extracted_skills_count,
    }
    meta_path = research_dir / f"{stem}.meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    docs_mirror: str | None = None
    if mirror_docs:
        project_root = opc_dir.parent
        docs_research = project_root / "docs" / "research"
        try:
            docs_research.mkdir(parents=True, exist_ok=True)
            mirror_file = docs_research / f"{stem}.md"
            mirror_file.write_text(body, encoding="utf-8")
            docs_mirror = str(mirror_file)
        except OSError:
            docs_mirror = None

    if not quiet:
        print(f"\n📄 Research report: {md_path}")
        if docs_mirror:
            print(f"📄 Mirrored to: {docs_mirror}")

    return {
        **meta,
        "meta_path": str(meta_path),
        "docs_mirror": docs_mirror,
        "insights": [asdict(i) for i in insights[:20]],
    }


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="SuperOPC market research pipeline")
    parser.add_argument("--cwd", default=".", help="Project directory containing .opc/")
    parser.add_argument("--query", required=True, help="Research topic / niche")
    parser.add_argument("--days", type=int, default=30)
    parser.add_argument("--subreddit", default="")
    parser.add_argument("--sources", default="", help="Comma-separated: github,reddit,hackernews,producthunt")
    parser.add_argument("--no-mirror-docs", action="store_true", help="Skip docs/research mirror")
    parser.add_argument("--no-extract-skills", action="store_true", help="Skip writing .opc/intelligence/extracted-skills/")
    parser.add_argument("--json", action="store_true", help="Print result JSON to stdout")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    opc_d = cwd / ".opc"
    if not opc_d.is_dir():
        for parent in [cwd, *cwd.parents]:
            if (parent / ".opc").is_dir():
                opc_d = parent / ".opc"
                break
        else:
            print("opc_research error: .opc/ not found", file=sys.stderr)
            sys.exit(1)

    sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
    result = run_market_research(
        opc_d,
        args.query,
        days=args.days,
        subreddit=args.subreddit,
        sources=sources,
        mirror_docs=not args.no_mirror_docs,
        extract_skills=not args.no_extract_skills,
        quiet=args.json,
    )
    if args.json:
        # Drop large insights for one-line JSON
        out = {k: v for k, v in result.items() if k != "insights"}
        out["insights_preview"] = len(result.get("insights", []))
        print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
