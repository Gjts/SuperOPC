from __future__ import annotations

import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from intelligence.insight_generator import Insight


def research_slug(value: str) -> str:
    normalized = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value.strip().lower())
    normalized = re.sub(r"-+", "-", normalized).strip("-")
    return (normalized or "research")[:60]


def _truncate(text: str, limit: int = 200) -> str:
    if len(text) <= limit:
        return text
    return f"{text[:limit]}..."


def render_research_markdown(
    *,
    query: str,
    generated_at: str,
    feed_report: dict[str, Any],
    insights: list[Insight],
    methodologies: list[dict[str, Any]],
) -> str:
    lines = [
        f"## Research Report: {query}",
        "",
        f"**Generated At (UTC):** {generated_at}",
        f"**Sources Succeeded:** {', '.join(feed_report.get('sources_succeeded', [])) or 'none'}",
        f"**Guardrail Status:** {feed_report.get('guardrail_status') or 'unknown'}",
        "",
        "### Key Findings",
        "",
    ]

    for insight in insights[:12]:
        lines.append(f"- **[{insight.source}]** {insight.title} _(score {insight.relevance_score:.2f})_")
        lines.append(f"  - {_truncate(insight.summary)}")
        for action in insight.action_items[:2]:
            lines.append(f"  - -> {action}")
        lines.append("")

    lines.extend(["### Methodology Lens", ""])
    if methodologies:
        for item in methodologies:
            lines.append(f"- **{item.get('name', '')}** ({item.get('domain', '')}) - {item.get('one_liner', '')}")
            steps = item.get("steps_summary") or []
            if steps:
                lines.append(f"  - Steps: {'; '.join(str(step) for step in steps[:3])}")
            if item.get("anchor_quote"):
                lines.append(f"  - _{item['anchor_quote']}_")
            lines.append("")
    else:
        lines.append("_No methodology matched. Extend `.opc/intelligence/methodologies/` if needed._")
        lines.append("")

    lines.extend(
        [
            "### Recommended Actions",
            "1. Run `opc-tools research insights --cwd <project>` to refresh structured insight JSON.",
            "2. Cross-check the highest-signal findings with `references/business/validate-idea.md` or `references/intelligence/market-research.md`.",
            "3. Record any unverified assumptions in the plan's `opc-assumptions-analyzer` section.",
            "",
        ]
    )
    return "\n".join(lines)


def persist_research_report(
    *,
    opc_dir: Path,
    stem: str,
    query: str,
    generated_at: str,
    feed_path: Path,
    feed_report: dict[str, Any],
    body: str,
    insights: list[Insight],
    methodologies: list[dict[str, Any]],
    extracted_skills_dir: Path,
    extracted_skills_count: int,
    mirror_docs: bool,
) -> dict[str, Any]:
    research_dir = opc_dir / "research"
    research_dir.mkdir(parents=True, exist_ok=True)

    md_path = research_dir / f"{stem}.md"
    md_path.write_text(body, encoding="utf-8")

    meta = {
        "query": query,
        "generated_at": generated_at,
        "feed_path": str(feed_path),
        "markdown_path": str(md_path),
        "sources_succeeded": feed_report.get("sources_succeeded", []),
        "guardrail_status": feed_report.get("guardrail_status"),
        "insights_count": len(insights),
        "methodologies": [item.get("name") for item in methodologies],
        "extracted_skills_dir": str(extracted_skills_dir),
        "extracted_skills_count": extracted_skills_count,
    }

    meta_path = research_dir / f"{stem}.meta.json"
    meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")

    docs_mirror: str | None = None
    if mirror_docs:
        docs_research = opc_dir.parent / "docs" / "research"
        try:
            docs_research.mkdir(parents=True, exist_ok=True)
            mirror_file = docs_research / f"{stem}.md"
            mirror_file.write_text(body, encoding="utf-8")
            docs_mirror = str(mirror_file)
        except OSError:
            docs_mirror = None

    return {
        **meta,
        "meta_path": str(meta_path),
        "docs_mirror": docs_mirror,
        "insights": [asdict(item) for item in insights[:20]],
    }


def render_research_notice(markdown_path: str, docs_mirror: str | None) -> str:
    lines = [f"Research report: {markdown_path}"]
    if docs_mirror:
        lines.append(f"Mirrored to: {docs_mirror}")
    return "\n".join(lines)


def build_research_preview(result: dict[str, Any], *, preview_key: str) -> dict[str, Any]:
    preview = {key: value for key, value in result.items() if key != "insights"}
    preview[preview_key] = len(result.get("insights", []))
    return preview


def render_insights_preview(payload: dict[str, Any], *, limit: int = 5) -> str:
    insights = payload.get("insights", [])
    count = int(payload.get("count", len(insights) if isinstance(insights, list) else 0))
    lines = [f"Research insights: {count}"]
    if not isinstance(insights, list) or not insights:
        lines.append("No insights generated.")
        return "\n".join(lines)

    for item in insights[:limit]:
        if not isinstance(item, dict):
            continue
        source = str(item.get("source", "unknown"))
        title = str(item.get("title", "Untitled insight"))
        score = item.get("relevance_score")
        score_text = f" (score {score})" if score is not None else ""
        lines.append(f"- [{source}] {title}{score_text}")
        actions = item.get("action_items")
        if isinstance(actions, list) and actions:
            lines.append(f"  next: {', '.join(str(action) for action in actions[:2])}")

    remaining = count - min(count, limit)
    if remaining > 0:
        lines.append(f"... and {remaining} more")
    return "\n".join(lines)
