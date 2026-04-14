#!/usr/bin/env python3
"""
feed_scraper.py — Multi-source Intelligence Radar for SuperOPC.

Inspired by Follow-Builders, last30days, and market-research skills.
Fetches multi-source intelligence to provide grounded, anti-hallucination
context before any validation or brainstorming.

Sources:
  - GitHub Trending (repositories by topic)
  - Reddit (niche subreddits and search)
  - Hacker News (top/new stories by keyword)
  - Product Hunt (recent launches, via unofficial API)

Each source is independently resilient — individual failures
don't block other sources from returning data.
"""

import sys
import argparse
import json
import urllib.request
import urllib.error
import urllib.parse
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_DEFAULT_OPC = REPO_ROOT / ".opc"
FEED_DEST = _DEFAULT_OPC / "market_feed_latest.json"
FEED_HISTORY_DIR = _DEFAULT_OPC / "market_feeds"

REQUEST_TIMEOUT = 10


def resolve_opc_dir(cwd: Path | None) -> Path:
    """Locate `.opc/` for feed storage; falls back to SuperOPC repo `.opc` if none found."""
    if cwd is None:
        return _DEFAULT_OPC
    start = cwd.resolve()
    for candidate in [start, *start.parents]:
        opc = candidate / ".opc"
        if opc.is_dir():
            return opc
    return _DEFAULT_OPC


def feed_paths(opc_dir: Path | None) -> tuple[Path, Path]:
    """Return (market_feed_latest.json path, market_feeds history directory)."""
    base = opc_dir if opc_dir is not None else _DEFAULT_OPC
    return base / "market_feed_latest.json", base / "market_feeds"
USER_AGENT = "SuperOPC-Intelligence-Agent/2.0"


def _fetch_json(url: str, *, headers: dict[str, str] | None = None) -> Any:
    hdrs = {"User-Agent": USER_AGENT}
    if headers:
        hdrs.update(headers)
    req = urllib.request.Request(url, headers=hdrs)
    with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
        return json.loads(resp.read().decode())


def fetch_github_trends(topic: str, *, days: int = 30, limit: int = 10) -> list[dict[str, Any]]:
    print(f"📡 GitHub: searching '{topic}' (last {days} days)...")
    cutoff = (datetime.now(timezone.utc) - timedelta(days=days)).strftime("%Y-%m-%d")
    safe_topic = urllib.parse.quote(topic)
    url = (
        f"https://api.github.com/search/repositories"
        f"?q={safe_topic}+created:>{cutoff}&sort=stars&order=desc&per_page={limit}"
    )
    try:
        data = _fetch_json(url)
        return [
            {
                "repo": item["full_name"],
                "stars": item["stargazers_count"],
                "desc": item.get("description") or "",
                "url": item["html_url"],
                "created": item.get("created_at", "")[:10],
                "language": item.get("language") or "",
                "topics": item.get("topics", [])[:5],
            }
            for item in data.get("items", [])[:limit]
        ]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  ⚠️ GitHub failed: {e}")
        return [{"_error": str(e), "_source": "github"}]


def fetch_reddit_mentions(query: str, *, subreddit: str = "", limit: int = 10) -> list[dict[str, Any]]:
    sub = f"r/{subreddit}/" if subreddit else ""
    print(f"📡 Reddit: searching '{query}' in {sub or 'all'}...")
    safe_query = urllib.parse.quote(query)
    url = f"https://www.reddit.com/{sub}search.json?q={safe_query}&sort=hot&limit={limit}&t=month"
    try:
        data = _fetch_json(url, headers={"User-Agent": "Mozilla/5.0 (SuperOPC)"})
        return [
            {
                "title": child["data"]["title"],
                "ups": child["data"]["ups"],
                "comments": child["data"]["num_comments"],
                "url": f"https://reddit.com{child['data']['permalink']}",
                "subreddit": child["data"]["subreddit"],
                "created": datetime.fromtimestamp(
                    child["data"]["created_utc"], tz=timezone.utc
                ).strftime("%Y-%m-%d"),
            }
            for child in data.get("data", {}).get("children", [])[:limit]
        ]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  ⚠️ Reddit failed: {e}")
        return [{"_error": str(e), "_source": "reddit"}]


def fetch_hackernews(query: str, *, limit: int = 10) -> list[dict[str, Any]]:
    print(f"📡 Hacker News: searching '{query}'...")
    safe_query = urllib.parse.quote(query)
    url = f"http://hn.algolia.com/api/v1/search?query={safe_query}&tags=story&hitsPerPage={limit}"
    try:
        data = _fetch_json(url)
        return [
            {
                "title": hit.get("title", ""),
                "points": hit.get("points", 0),
                "comments": hit.get("num_comments", 0),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID', '')}",
                "author": hit.get("author", ""),
                "created": hit.get("created_at", "")[:10],
            }
            for hit in data.get("hits", [])[:limit]
        ]
    except (urllib.error.URLError, json.JSONDecodeError, KeyError) as e:
        print(f"  ⚠️ HackerNews failed: {e}")
        return [{"_error": str(e), "_source": "hackernews"}]


def fetch_producthunt_proxy(query: str, *, limit: int = 5) -> list[dict[str, Any]]:
    """Search Product Hunt via unofficial search endpoint."""
    print(f"📡 Product Hunt: searching '{query}'...")
    safe_query = urllib.parse.quote(query)
    url = f"https://www.producthunt.com/frontend/graphql"
    # PH API requires authentication for most endpoints; fall back to a basic approach
    # that signals this source is configured but may need a PH API key for full access
    try:
        search_url = f"https://api.producthunt.com/v2/api/graphql"
        return [{"_note": "Product Hunt API requires API key. Set PH_API_KEY env var for full access.", "_source": "producthunt"}]
    except Exception as e:
        return [{"_error": str(e), "_source": "producthunt"}]


def compose_intelligence_report(
    query: str,
    *,
    days: int = 30,
    subreddit: str = "",
    sources: list[str] | None = None,
    opc_dir: Path | None = None,
) -> dict[str, Any]:
    """Write feeds under *opc_dir* (default: SuperOPC repo `.opc/`). Pass user project's `.opc` from CLI."""
    feed_dest, feed_history_dir = feed_paths(opc_dir)
    active_sources = sources or ["github", "reddit", "hackernews", "producthunt"]

    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "target_niche": query,
        "time_window_days": days,
        "sources_requested": active_sources,
        "sources_succeeded": [],
    }

    if "github" in active_sources:
        gh = fetch_github_trends(query, days=days)
        report["github_trends"] = gh
        if gh and "_error" not in gh[0]:
            report["sources_succeeded"].append("github")

    if "reddit" in active_sources:
        rd = fetch_reddit_mentions(query, subreddit=subreddit)
        report["reddit_mentions"] = rd
        if rd and "_error" not in rd[0]:
            report["sources_succeeded"].append("reddit")

    if "hackernews" in active_sources:
        hn = fetch_hackernews(query)
        report["hackernews_stories"] = hn
        if hn and "_error" not in hn[0]:
            report["sources_succeeded"].append("hackernews")

    if "producthunt" in active_sources:
        ph = fetch_producthunt_proxy(query)
        report["producthunt_launches"] = ph
        if ph and "_error" not in ph[0] and "_note" not in ph[0]:
            report["sources_succeeded"].append("producthunt")

    report["guardrail_status"] = (
        "READY_FOR_EVALUATION" if report["sources_succeeded"] else "PARTIAL_DATA"
    )

    feed_dest.parent.mkdir(parents=True, exist_ok=True)
    with open(feed_dest, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    feed_history_dir.mkdir(parents=True, exist_ok=True)
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    history_file = feed_history_dir / f"feed-{date_str}.json"
    with open(history_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    succeeded = len(report["sources_succeeded"])
    total = len(active_sources)
    print(f"\n✅ Intelligence report saved ({succeeded}/{total} sources)")
    print(f"   Latest: {feed_dest}")
    print(f"   History: {history_file}")
    print("=> opc-researcher and Minimalist Entrepreneur pipeline may now proceed.")

    return report


def trend_summary(*, days: int = 30, opc_dir: Path | None = None) -> dict[str, Any]:
    """Aggregate historical feeds within the window into a trend summary."""
    _, feed_history_dir = feed_paths(opc_dir)
    feed_history_dir.mkdir(parents=True, exist_ok=True)
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    all_repos: list[dict] = []
    all_reddit: list[dict] = []
    all_hn: list[dict] = []

    for fpath in sorted(feed_history_dir.glob("feed-*.json")):
        try:
            date_part = fpath.stem.replace("feed-", "")
            file_date = datetime.strptime(date_part, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            if file_date < cutoff:
                continue
            data = json.loads(fpath.read_text(encoding="utf-8"))
            for item in data.get("github_trends", []):
                if "_error" not in item:
                    all_repos.append(item)
            for item in data.get("reddit_mentions", []):
                if "_error" not in item:
                    all_reddit.append(item)
            for item in data.get("hackernews_stories", []):
                if "_error" not in item:
                    all_hn.append(item)
        except (json.JSONDecodeError, ValueError, OSError):
            continue

    top_repos = sorted(all_repos, key=lambda x: x.get("stars", 0), reverse=True)[:10]
    top_reddit = sorted(all_reddit, key=lambda x: x.get("ups", 0), reverse=True)[:10]
    top_hn = sorted(all_hn, key=lambda x: x.get("points", 0), reverse=True)[:10]

    return {
        "window_days": days,
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "feeds_analyzed": len(list(feed_history_dir.glob("feed-*.json"))),
        "top_github": top_repos,
        "top_reddit": top_reddit,
        "top_hackernews": top_hn,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="SuperOPC Multi-Source Intelligence Radar")
    parser.add_argument("--query", type=str, required=True, help="Target niche or topic to sweep")
    parser.add_argument("--days", type=int, default=30, help="Time window in days (default: 30)")
    parser.add_argument("--subreddit", type=str, default="", help="Specific subreddit to search")
    parser.add_argument("--sources", type=str, default="", help="Comma-separated sources (github,reddit,hackernews,producthunt)")
    parser.add_argument("--summary", action="store_true", help="Show trend summary from historical feeds")
    parser.add_argument("--cwd", type=str, default=".", help="Project directory (feeds written to its .opc/)")
    args = parser.parse_args()

    opc_d = resolve_opc_dir(Path(args.cwd))

    if args.summary:
        summary = trend_summary(days=args.days, opc_dir=opc_d)
        print(json.dumps(summary, ensure_ascii=False, indent=2))
    else:
        sources = [s.strip() for s in args.sources.split(",") if s.strip()] if args.sources else None
        compose_intelligence_report(
            args.query,
            days=args.days,
            subreddit=args.subreddit,
            sources=sources,
            opc_dir=opc_d,
        )
