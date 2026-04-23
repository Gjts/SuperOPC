"""
research.py — Market intelligence pipeline opc-tools domain.
"""

from __future__ import annotations

from pathlib import Path

from cli.core import error, opc_dir, output
from cli.router import parse_named_args
from research_helpers import build_research_preview, render_insights_preview


def dispatch_research(args: list[str], cwd: Path, raw: bool) -> None:
    if not args:
        error("research subcommand required: feed | insights | methods | run")
    sub = args[0]
    rest = args[1:]

    if sub == "feed":
        cmd_research_feed(cwd, rest, raw)
    elif sub == "insights":
        cmd_research_insights(cwd, rest, raw)
    elif sub == "methods":
        cmd_research_methods(cwd, rest, raw)
    elif sub == "run":
        cmd_research_run(cwd, rest, raw)
    else:
        error("Unknown research subcommand\nAvailable: feed, insights, methods, run")


def cmd_research_feed(cwd: Path, rest: list[str], raw: bool) -> None:
    from intelligence.feed_scraper import compose_intelligence_report

    named = parse_named_args(
        rest,
        value_flags=["query", "days", "subreddit", "sources"],
        bool_flags=[],
    )
    q = named.get("query")
    if not isinstance(q, str) or not q.strip():
        error("research feed requires --query <topic>")
    days = int(named["days"]) if named.get("days") and str(named["days"]).isdigit() else 30
    subreddit = (named.get("subreddit") or "") if isinstance(named.get("subreddit"), str) else ""
    src = named.get("sources")
    sources = None
    if isinstance(src, str) and src.strip():
        sources = [s.strip() for s in src.split(",") if s.strip()]
    opc_d = opc_dir(cwd)
    report = compose_intelligence_report(
        q.strip(),
        days=days,
        subreddit=subreddit,
        sources=sources,
        opc_dir=opc_d,
    )
    output(
        {
            "ok": True,
            "sources_succeeded": report.get("sources_succeeded"),
            "guardrail_status": report.get("guardrail_status"),
            "target_niche": report.get("target_niche"),
        },
        raw,
        report.get("guardrail_status", "ok"),
    )


def cmd_research_insights(cwd: Path, rest: list[str], raw: bool) -> None:
    from intelligence.insight_generator import InsightGenerator

    named = parse_named_args(rest, value_flags=["feed"], bool_flags=[])
    opc_d = opc_dir(cwd)
    gen = InsightGenerator(opc_d)
    feed_arg = named.get("feed")
    if isinstance(feed_arg, str) and feed_arg.strip():
        feed_path = Path(feed_arg.strip())
        if not feed_path.is_absolute():
            feed_path = cwd / feed_path
        insights = gen.process_feed(feed_path)
    else:
        insights = gen.process_latest()
    payload = {
        "count": len(insights),
        "insights": [
            {
                "id": i.id,
                "source": i.source,
                "title": i.title,
                "relevance_score": i.relevance_score,
                "action_items": i.action_items[:5],
            }
            for i in insights[:30]
        ],
    }
    output(payload, raw, render_insights_preview(payload))


def cmd_research_methods(cwd: Path, rest: list[str], raw: bool) -> None:
    from intelligence.methodology_database import MethodologyDatabase

    if not rest:
        error("research methods requires: list | show <id>")
    opc_d = opc_dir(cwd)
    db = MethodologyDatabase(db_dir=opc_d / "intelligence" / "methodologies")

    if rest[0] == "list":
        named = parse_named_args(rest[1:], value_flags=["domain", "keyword", "tags"], bool_flags=[])
        domain = (named.get("domain") or "") if isinstance(named.get("domain"), str) else ""
        keyword = (named.get("keyword") or "") if isinstance(named.get("keyword"), str) else ""
        tags_s = named.get("tags")
        tags = None
        if isinstance(tags_s, str) and tags_s.strip():
            tags = [t.strip() for t in tags_s.split(",") if t.strip()]
        rows = db.query(domain=domain, keyword=keyword, tags=tags, limit=50)
        output(
            {
                "methodologies": [{"id": m.id, "name": m.name, "domain": m.domain} for m in rows],
            },
            raw,
            None,
        )
    elif rest[0] == "show":
        if len(rest) < 2:
            error("research methods show <id>")
        m = db.get(rest[1])
        if m is None:
            output({"found": False, "id": rest[1]}, raw, "not found")
        from dataclasses import asdict

        output({"found": True, "methodology": asdict(m)}, raw, None)
    else:
        error("research methods: use list | show <id>")


def cmd_research_run(cwd: Path, rest: list[str], raw: bool) -> None:
    from opc_research import run_market_research

    named = parse_named_args(
        rest,
        value_flags=["query", "days", "subreddit", "sources"],
        bool_flags=["no-mirror-docs", "no-extract-skills"],
    )
    q = named.get("query")
    if not isinstance(q, str) or not q.strip():
        error("research run requires --query <topic>")
    days = int(named["days"]) if named.get("days") and str(named["days"]).isdigit() else 30
    subreddit = (named.get("subreddit") or "") if isinstance(named.get("subreddit"), str) else ""
    src = named.get("sources")
    sources = None
    if isinstance(src, str) and src.strip():
        sources = [s.strip() for s in src.split(",") if s.strip()]
    opc_d = opc_dir(cwd)
    mirror = not bool(named.get("no-mirror-docs"))
    extract_skills = not bool(named.get("no-extract-skills"))
    result = run_market_research(
        opc_d,
        q.strip(),
        days=days,
        subreddit=subreddit,
        sources=sources,
        mirror_docs=mirror,
        extract_skills=extract_skills,
        quiet=True,
    )
    slim = build_research_preview(result, preview_key="insights_preview_count")
    output(slim, raw, result.get("markdown_path", "ok"))
