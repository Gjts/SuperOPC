#!/usr/bin/env python3
"""
insight_generator.py — Actionable intelligence extraction for SuperOPC v2.

Takes raw intelligence data (from feed_scraper.py or external sources)
and generates structured, actionable insights.  Integrates with the
event bus and learning store.
"""

from __future__ import annotations

import json
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "engine"))

from event_bus import EventBus, get_event_bus


# ---------------------------------------------------------------------------
# Insight model
# ---------------------------------------------------------------------------

@dataclass
class Insight:
    id: str = ""
    source: str = ""
    category: str = "market"
    title: str = ""
    summary: str = ""
    relevance_score: float = 0.0
    action_items: list[str] = field(default_factory=list)
    raw_data_ref: str = ""
    generated_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
    )


# ---------------------------------------------------------------------------
# InsightGenerator
# ---------------------------------------------------------------------------

class InsightGenerator:
    """Processes raw intel feeds and produces actionable insights."""

    def __init__(self, opc_dir: Path, bus: EventBus | None = None):
        self._opc_dir = opc_dir
        self._intel_dir = opc_dir / "intelligence"
        self._bus = bus or get_event_bus()

    def process_feed(self, feed_path: Path) -> list[Insight]:
        try:
            data = json.loads(feed_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return []

        insights: list[Insight] = []
        niche = data.get("target_niche", "unknown")

        github_trends = data.get("github_trends", [])
        for item in github_trends:
            if "_error" in item or "error" in item:
                continue
            stars = item.get("stars", 0)
            relevance = min(1.0, stars / 10000) if stars else 0.1
            insight = Insight(
                id=f"gh-{item.get('repo', 'unknown').replace('/', '-')}",
                source="github",
                category="competitive",
                title=f"Trending: {item.get('repo', 'unknown')} ({stars} stars)",
                summary=item.get("desc", "No description") or "No description",
                relevance_score=relevance,
                action_items=self._derive_github_actions(item, niche),
                raw_data_ref=str(feed_path),
            )
            insights.append(insight)

        reddit_mentions = data.get("reddit_mentions", [])
        for item in reddit_mentions:
            if "_error" in item or "error" in item:
                continue
            ups = item.get("ups", 0)
            relevance = min(1.0, ups / 500) if ups else 0.05
            insight = Insight(
                id=f"reddit-{hash(item.get('title', '')):#010x}",
                source="reddit",
                category="market_signal",
                title=f"Discussion: {item.get('title', 'unknown')[:80]}",
                summary=f"Upvotes: {ups} | Comments: {item.get('comments', 0)} | r/{item.get('subreddit', '')}",
                relevance_score=relevance,
                action_items=self._derive_reddit_actions(item, niche),
                raw_data_ref=str(feed_path),
            )
            insights.append(insight)

        hn_stories = data.get("hackernews_stories", [])
        for item in hn_stories:
            if "_error" in item:
                continue
            points = item.get("points", 0)
            relevance = min(1.0, points / 300) if points else 0.05
            insight = Insight(
                id=f"hn-{hash(item.get('title', '')):#010x}",
                source="hackernews",
                category="technical_signal",
                title=f"HN: {item.get('title', 'unknown')[:80]}",
                summary=f"Points: {points} | Comments: {item.get('comments', 0)} | by {item.get('author', '')}",
                relevance_score=relevance,
                action_items=self._derive_hn_actions(item, niche),
                raw_data_ref=str(feed_path),
            )
            insights.append(insight)

        insights.sort(key=lambda i: i.relevance_score, reverse=True)
        self._persist_insights(insights)

        if insights:
            top = insights[0]
            self._bus.publish("market.update", {
                "insights_count": len(insights),
                "top_insight": top.title,
                "niche": niche,
            }, source="insight_generator")

        return insights

    def process_latest(self) -> list[Insight]:
        feed_file = self._opc_dir / "market_feed_latest.json"
        if not feed_file.exists():
            return []
        return self.process_feed(feed_file)

    def get_top_insights(self, n: int = 5) -> list[dict[str, Any]]:
        all_insights = self._load_persisted()
        top = sorted(all_insights, key=lambda i: i.get("relevance_score", 0), reverse=True)[:n]
        return top

    @staticmethod
    def _derive_github_actions(item: dict[str, Any], niche: str) -> list[str]:
        actions = []
        stars = item.get("stars", 0)
        if stars > 5000:
            actions.append(f"Evaluate {item.get('repo')} as potential competitor or integration target")
        if stars > 1000:
            actions.append(f"Study {item.get('repo')} architecture for inspiration")
        actions.append(f"Monitor {item.get('repo')} for feature overlap with {niche}")
        return actions

    @staticmethod
    def _derive_reddit_actions(item: dict[str, Any], niche: str) -> list[str]:
        actions = []
        ups = item.get("ups", 0)
        if ups > 100:
            actions.append(f"Analyze discussion sentiment for {niche} market validation")
        actions.append("Extract pain points mentioned in community discussions")
        return actions

    @staticmethod
    def _derive_hn_actions(item: dict[str, Any], niche: str) -> list[str]:
        actions = []
        points = item.get("points", 0)
        if points > 100:
            actions.append(f"High-signal HN discussion — analyze for {niche} technical trends")
        if item.get("comments", 0) > 50:
            actions.append("Extract expert opinions and counter-arguments from comments")
        actions.append(f"Evaluate relevance to {niche} product direction")
        return actions

    def _persist_insights(self, insights: list[Insight]) -> None:
        self._intel_dir.mkdir(parents=True, exist_ok=True)
        date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        filepath = self._intel_dir / f"insights-{date_str}.json"
        data = [asdict(i) for i in insights]
        filepath.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _load_persisted(self) -> list[dict[str, Any]]:
        if not self._intel_dir.exists():
            return []
        all_data: list[dict[str, Any]] = []
        for filepath in sorted(self._intel_dir.glob("insights-*.json"), reverse=True)[:7]:
            try:
                items = json.loads(filepath.read_text(encoding="utf-8"))
                if isinstance(items, list):
                    all_data.extend(items)
            except (json.JSONDecodeError, OSError):
                continue
        return all_data


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="SuperOPC Insight Generator")
    parser.add_argument("--cwd", default=".", help="Project directory containing .opc/")
    parser.add_argument("--feed", default="", help="Path to feed JSON file (default: .opc/market_feed_latest.json)")
    parser.add_argument("--top", type=int, default=5, help="Show top N insights")
    args = parser.parse_args()

    cwd = Path(args.cwd).resolve()
    opc_dir = cwd / ".opc"
    if not opc_dir.exists():
        for parent in cwd.parents:
            candidate = parent / ".opc"
            if candidate.exists():
                opc_dir = candidate
                break

    generator = InsightGenerator(opc_dir)

    if args.feed:
        insights = generator.process_feed(Path(args.feed))
    else:
        insights = generator.process_latest()

    if insights:
        print(f"Generated {len(insights)} insights:")
        for insight in insights[:args.top]:
            print(f"  [{insight.relevance_score:.2f}] {insight.title}")
            for action in insight.action_items:
                print(f"    -> {action}")
    else:
        print("No insights generated. Run feed_scraper.py first to collect raw data.")


if __name__ == "__main__":
    main()
