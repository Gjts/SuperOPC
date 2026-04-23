from __future__ import annotations

import json
from pathlib import Path

from intelligence.insight_generator import Insight
from research_helpers import (
    build_research_preview,
    persist_research_report,
    render_insights_preview,
    render_research_markdown,
    render_research_notice,
    research_slug,
)


def sample_insight(*, summary: str = "Pain points collected from users.") -> Insight:
    return Insight(
        id="i-1",
        source="reddit",
        category="market_signal",
        title="Users keep asking for onboarding help",
        summary=summary,
        relevance_score=0.82,
        action_items=["Interview power users", "Compare competing onboarding flows"],
        raw_data_ref=".opc/market_feed_latest.json",
        generated_at="2026-04-23T00:00:00Z",
    )


def test_research_slug_preserves_chinese_and_falls_back() -> None:
    assert research_slug("  Viral Referral Loop  ") == "viral-referral-loop"
    assert research_slug("增长 飞轮") == "增长-飞轮"
    assert research_slug("!!!") == "research"


def test_render_research_markdown_includes_sections_and_truncates_summary() -> None:
    markdown = render_research_markdown(
        query="Growth loop",
        generated_at="2026-04-23T00:00:00Z",
        feed_report={"sources_succeeded": ["reddit", "github"], "guardrail_status": "ok"},
        insights=[sample_insight(summary="x" * 205)],
        methodologies=[
            {
                "name": "JTBD",
                "domain": "product",
                "one_liner": "Map user struggles to actionable jobs.",
                "steps_summary": ["Interview", "Cluster", "Prioritize"],
                "anchor_quote": "Customers hire products to make progress.",
            }
        ],
    )

    assert "## Research Report: Growth loop" in markdown
    assert "**Sources Succeeded:** reddit, github" in markdown
    assert "### Key Findings" in markdown
    assert "### Methodology Lens" in markdown
    assert "### Recommended Actions" in markdown
    assert ("x" * 200) + "..." in markdown


def test_persist_research_report_writes_markdown_meta_and_docs_mirror(tmp_path: Path) -> None:
    project_root = tmp_path / "sample-project"
    opc_dir = project_root / ".opc"
    feed_path = opc_dir / "market_feed_latest.json"
    body = "# Report\n"

    result = persist_research_report(
        opc_dir=opc_dir,
        stem="2026-04-23-growth-loop",
        query="Growth loop",
        generated_at="2026-04-23T00:00:00Z",
        feed_path=feed_path,
        feed_report={"sources_succeeded": ["reddit"], "guardrail_status": "ok"},
        body=body,
        insights=[sample_insight()],
        methodologies=[{"name": "JTBD"}],
        extracted_skills_dir=opc_dir / "intelligence" / "extracted-skills",
        extracted_skills_count=2,
        mirror_docs=True,
    )

    markdown_path = Path(result["markdown_path"])
    meta_path = Path(result["meta_path"])
    docs_mirror = Path(result["docs_mirror"])

    assert markdown_path.exists()
    assert markdown_path.read_text(encoding="utf-8") == body
    assert meta_path.exists()
    assert docs_mirror.exists()

    meta = json.loads(meta_path.read_text(encoding="utf-8"))
    assert meta["query"] == "Growth loop"
    assert meta["insights_count"] == 1
    assert meta["extracted_skills_count"] == 2
    assert result["insights"][0]["title"] == "Users keep asking for onboarding help"


def test_build_research_preview_and_notice_stay_compact() -> None:
    result = {
        "query": "增长 飞轮",
        "markdown_path": "C:/项目/research.md",
        "docs_mirror": "C:/项目/docs/research.md",
        "insights": [{"id": "1"}, {"id": "2"}],
    }

    preview = build_research_preview(result, preview_key="insights_preview")
    notice = render_research_notice(result["markdown_path"], result["docs_mirror"])

    assert "insights" not in preview
    assert preview["insights_preview"] == 2
    assert notice == "Research report: C:/项目/research.md\nMirrored to: C:/项目/docs/research.md"

def test_render_insights_preview_surfaces_titles_scores_and_actions() -> None:
    preview = render_insights_preview(
        {
            "count": 2,
            "insights": [
                {
                    "source": "reddit",
                    "title": "Users ask for better onboarding",
                    "relevance_score": 0.82,
                    "action_items": ["Interview power users", "Compare top competitors"],
                },
                {
                    "source": "github",
                    "title": "Open-source workflow tooling is growing",
                    "relevance_score": 0.74,
                    "action_items": ["Review repo positioning"],
                },
            ],
        }
    )

    assert "Research insights: 2" in preview
    assert "[reddit] Users ask for better onboarding (score 0.82)" in preview
    assert "next: Interview power users, Compare top competitors" in preview
