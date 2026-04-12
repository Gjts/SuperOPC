---
name: opc-intel
description: Query market intelligence, view recent insights, and manage the intelligence pipeline.
---

# /opc-intel

## Usage

```
/opc-intel [query|status|refresh] [--top N] [--json]
```

## Sub-commands

### query (default)
Display top actionable insights from the intelligence pipeline.

```
/opc-intel --top 10
```

### status
Show intelligence pipeline status: last update time, insight counts, data sources.

```
/opc-intel status
```

### refresh
Trigger a fresh intelligence sweep (runs feed_scraper + insight_generator).

```
/opc-intel refresh
```

## Data Flow

```
feed_scraper.py → .opc/market_feed_latest.json → insight_generator.py → .opc/intelligence/insights-*.json
```

## Sources

- GitHub trending repositories
- Reddit community discussions
- Builder feeds (Follow Builders integration)
- Custom sources (configurable in .opc/config.json)

## Related

- `/opc-research` — Full market research workflow
- `/opc-cruise` — Cruise mode auto-refreshes intelligence on schedule
