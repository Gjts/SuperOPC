#!/usr/bin/env python3
"""
feed_scraper.py — Intelligence Radar for SuperOPC.
Inspired by Follow-Builders and last30days-skill.

This script fetches multi-source intelligence (e.g., GitHub trending, Reddit mentions)
to provide grounded, anti-hallucination context before any validation or brainstorming.
"""

import sys
import argparse
import json
import urllib.request
import urllib.error
import urllib.parse
from pathlib import Path
from datetime import datetime

if sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except AttributeError:
        pass

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
FEED_DEST = REPO_ROOT / ".opc" / "market_feed_latest.json"

def fetch_github_trends(topic: str) -> list:
    print(f"📡 Sweeping GitHub for topic: {topic}...")
    safe_topic = urllib.parse.quote(topic)
    url = f"https://api.github.com/search/repositories?q={safe_topic}+sort:stars-desc&per_page=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'SuperOPC-Intelligence-Agent'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return [{"repo": item["full_name"], "stars": item["stargazers_count"], "desc": item["description"], "url": item["html_url"]} for item in data.get("items", [])]
    except urllib.error.URLError as e:
        print(f"⚠️ Could not fetch GitHub: {e}")
        return [{"error": str(e), "note": "GitHub API limit reached or unreachable"}]

def fetch_reddit_mentions(query: str) -> list:
    print(f"📡 Sweeping Reddit for niche: {query}...")
    safe_query = urllib.parse.quote(query)
    url = f"https://www.reddit.com/search.json?q={safe_query}&sort=hot&limit=5"
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            data = json.loads(response.read().decode())
            return [{"title": child["data"]["title"], "ups": child["data"]["ups"], "url": child["data"]["url"]} for child in data.get("data", {}).get("children", [])]
    except urllib.error.URLError as e:
        print(f"⚠️ Could not fetch Reddit: {e}")
        return [{"error": str(e), "note": "Reddit API blocked or unreachable"}]

def compose_intelligence_report(query: str):
    github_data = fetch_github_trends(query)
    reddit_data = fetch_reddit_mentions(query)
    
    report = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "target_niche": query,
        "github_trends": github_data,
        "reddit_mentions": reddit_data,
        "guardrail_status": "READY_FOR_EVALUATION"
    }
    
    FEED_DEST.parent.mkdir(parents=True, exist_ok=True)
    with open(FEED_DEST, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    print(f"✅ Intelligence payload grounded and saved to {FEED_DEST}")
    print("=> opc-researcher and Minimalist Entrepreneur pipeline may now proceed with verified data.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Intelligence Radar Web Scraper")
    parser.add_argument("--query", type=str, required=True, help="The target niche or framework to sweep (e.g. 'ai agent workflow')")
    args = parser.parse_args()
    
    compose_intelligence_report(args.query)
