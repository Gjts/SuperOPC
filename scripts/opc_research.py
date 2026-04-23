#!/usr/bin/env python3
"""
opc_research.py - Market research pipeline: feed -> insights -> methodology -> Markdown.

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
from pathlib import Path
from typing import Any

from intelligence.feed_scraper import compose_intelligence_report, feed_paths
from intelligence.insight_generator import InsightGenerator
from intelligence.methodology_database import MethodologyDatabase
from intelligence.skill_extractor import SkillExtractor
from opc_common import find_opc_dir, now_iso
from research_helpers import (
    build_research_preview,
    persist_research_report,
    render_research_markdown,
    render_research_notice,
    research_slug,
)


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
    """Run scrape -> insights -> methodology summary -> Markdown under `.opc/research/`."""
    query = query.strip()
    if not query:
        raise ValueError("query is required")

    generated_at = now_iso()
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
    tags = [word for word in query.lower().split() if len(word) > 2][:8]
    methodologies = db.get_context_injection(tags=tags if tags else None, limit=4)
    if not methodologies:
        methodologies = db.get_context_injection(limit=4)

    extracted_skills_dir = opc_dir / "intelligence" / "extracted-skills"
    extracted_skills_count = 0
    if extract_skills:
        extractor = SkillExtractor(output_dir=extracted_skills_dir, verbose=not quiet)
        extracted = extractor.search_and_extract(query, limit=3, min_stars=1000)
        extracted_skills_count = len(extracted)

    stem = f"{generated_at[:10]}-{research_slug(query)}"
    body = render_research_markdown(
        query=query,
        generated_at=generated_at,
        feed_report=feed_report,
        insights=insights,
        methodologies=methodologies,
    )
    feed_dest, _ = feed_paths(opc_dir)
    result = persist_research_report(
        opc_dir=opc_dir,
        stem=stem,
        query=query,
        generated_at=generated_at,
        feed_path=feed_dest,
        feed_report=feed_report,
        body=body,
        insights=insights,
        methodologies=methodologies,
        extracted_skills_dir=extracted_skills_dir,
        extracted_skills_count=extracted_skills_count,
        mirror_docs=mirror_docs,
    )

    if not quiet:
        print()
        print(render_research_notice(result["markdown_path"], result["docs_mirror"]))

    return result


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
    opc_dir = find_opc_dir(cwd)
    if opc_dir is None:
        print("opc_research error: .opc/ not found", file=sys.stderr)
        sys.exit(1)

    sources = [item.strip() for item in args.sources.split(",") if item.strip()] if args.sources else None
    result = run_market_research(
        opc_dir,
        args.query,
        days=args.days,
        subreddit=args.subreddit,
        sources=sources,
        mirror_docs=not args.no_mirror_docs,
        extract_skills=not args.no_extract_skills,
        quiet=args.json,
    )
    if args.json:
        print(json.dumps(build_research_preview(result, preview_key="insights_preview"), ensure_ascii=True, indent=2))


if __name__ == "__main__":
    main()
