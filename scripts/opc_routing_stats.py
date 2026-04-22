#!/usr/bin/env python3
"""Aggregate ``.opc/routing/*.jsonl`` logs for Phase A observation window.

The Phase A intent router (``scripts/engine/intent_router.py``) appends a
JSONL record per ``route()`` call. After a 2-week observation window we
need four hard data points to lock Phase B decisions (D1-D4 listed in
``docs/plans/2026-05-05-skill-driven-runtime-phase-b.md``):

* **D1** — L2 embedding model: required iff ``L3 + fallback`` rate > 15 %.
* **D4** — embedding load timing: *lazy* is safe iff ``L1`` rate > 70 %.
* **latency budget** — can L2 (~20 ms) be added while p95 stays below
  50 ms? Current p95 answers this directly.

This script is intentionally **standalone** (no dependency on
``opc_insights``) so it can be called from ``pre-commit``, CI, or the
Phase B planning session without pulling in the 19 KB stats module.

Usage::

    python scripts/opc_routing_stats.py                     # last 30 days, text
    python scripts/opc_routing_stats.py --days 7 --json     # machine-readable
    python scripts/opc_routing_stats.py --since 2026-04-21  # custom window

Environment override::

    OPC_ROUTING_DIR=/tmp/sandbox-routing python scripts/opc_routing_stats.py
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from collections import Counter
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Iterable, Iterator

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_ROUTING_DIR = REPO_ROOT / ".opc" / "routing"

# Phase B decision thresholds (see docs/plans/2026-05-05-...-phase-b.md §D1/D4).
L3_FALLBACK_JUSTIFIES_L2 = 0.15  # L3+fallback rate above which L2 is worth the cost
L1_DOMINANT_FOR_LAZY = 0.70      # L1 hit rate above which lazy-load is safe
LOW_CONFIDENCE_CUTOFF = 0.2      # below which a route is considered miss-ish
FALLBACK_SKILL_ID = "using-superopc"


# ---------------------------------------------------------------------------
# Record iteration
# ---------------------------------------------------------------------------


def iter_records(
    routing_dir: Path,
    since: date | None,
    until: date | None,
) -> Iterator[dict[str, Any]]:
    """Yield records from ``<routing_dir>/YYYY-MM-DD.jsonl`` files.

    * File names not matching ``YYYY-MM-DD`` are ignored.
    * ``since`` / ``until`` are inclusive date bounds on the file name.
    * Malformed JSON lines are skipped silently so a single corrupted
      line never poisons the whole report.
    """
    if not routing_dir.exists() or not routing_dir.is_dir():
        return

    for file in sorted(routing_dir.glob("*.jsonl")):
        try:
            file_date = date.fromisoformat(file.stem)
        except ValueError:
            continue
        if since is not None and file_date < since:
            continue
        if until is not None and file_date > until:
            continue
        try:
            with file.open("r", encoding="utf-8") as fh:
                for line in fh:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        yield json.loads(line)
                    except json.JSONDecodeError:
                        continue
        except OSError:
            continue


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _is_fallback(record: dict[str, Any]) -> bool:
    """A fallback is the 3-tier miss: lands on using-superopc with conf 0."""
    return (
        record.get("skill_id") == FALLBACK_SKILL_ID
        and float(record.get("confidence", 0)) == 0.0
    )


def _classify_tier(record: dict[str, Any]) -> str:
    path = tuple(record.get("path") or ())
    if _is_fallback(record):
        return "fallback"
    if "L3" in path:
        return "L3"
    if "L2" in path:  # reserved for Phase B; Phase A never emits this
        return "L2"
    if "L1" in path:
        return "L1"
    return "unknown"


def _percentile(values: list[float], p: int) -> float:
    if not values:
        return 0.0
    idx = min(int(len(values) * p / 100), len(values) - 1)
    return round(values[idx], 3)


def aggregate(
    records: Iterable[dict[str, Any]],
    top_n: int = 5,
) -> dict[str, Any]:
    """Summarise an iterable of routing records.

    The returned dict is JSON-serialisable and stable between runs (keys
    always present; never uses :class:`set` or :class:`datetime`).
    """
    records = list(records)
    total = len(records)
    if total == 0:
        return {
            "total_routes": 0,
            "date_range": None,
            "tier_distribution": {},
            "latency_ms": {},
            "top_skills": [],
            "miss_analysis": {},
        }

    # Date range (string comparison works for ISO 8601)
    ts_values = [r.get("ts", "") for r in records if r.get("ts")]
    ts_values.sort()
    date_range = {
        "since": (ts_values[0][:10] if ts_values else ""),
        "until": (ts_values[-1][:10] if ts_values else ""),
    } if ts_values else None

    # Tier distribution
    tier_counts: Counter[str] = Counter(_classify_tier(r) for r in records)
    tier_distribution = {
        tier: {"count": count, "rate": round(count / total, 4)}
        for tier, count in tier_counts.most_common()
    }

    # Latency percentiles
    latencies = sorted(float(r.get("latency_ms", 0) or 0) for r in records)
    latency_ms = {
        "avg": round(sum(latencies) / len(latencies), 3),
        "p50": _percentile(latencies, 50),
        "p95": _percentile(latencies, 95),
        "p99": _percentile(latencies, 99),
        "max": round(latencies[-1], 3),
    }

    # Top skills (exclude fallback to avoid ``using-superopc`` dominating)
    skill_counts: Counter[str] = Counter(
        r.get("skill_id") for r in records if not _is_fallback(r)
    )
    top_skills = [
        {
            "skill_id": skill_id,
            "count": count,
            "rate": round(count / total, 4),
        }
        for skill_id, count in skill_counts.most_common(top_n)
    ]

    # Miss analysis
    low_conf = [
        r for r in records
        if float(r.get("confidence", 0) or 0) < LOW_CONFIDENCE_CUTOFF
    ]
    l3_rescued = [
        r for r in records
        if "L3" in (r.get("path") or ()) and not _is_fallback(r)
    ]
    fallback_count = tier_counts.get("fallback", 0)
    miss_analysis = {
        "low_confidence_count": len(low_conf),
        "low_confidence_rate": round(len(low_conf) / total, 4),
        "l3_rescued_count": len(l3_rescued),
        "l3_rescued_rate": round(len(l3_rescued) / total, 4),
        "fallback_count": fallback_count,
        "fallback_rate": round(fallback_count / total, 4),
    }

    return {
        "total_routes": total,
        "date_range": date_range,
        "tier_distribution": tier_distribution,
        "latency_ms": latency_ms,
        "top_skills": top_skills,
        "miss_analysis": miss_analysis,
    }


# ---------------------------------------------------------------------------
# Phase B decision recommendations
# ---------------------------------------------------------------------------


def phase_b_recommendations(agg: dict[str, Any]) -> list[str]:
    """Map aggregate metrics to actionable Phase B D1/D4/latency hints."""
    if agg.get("total_routes", 0) == 0:
        return [
            "No routing records in window. "
            "Trigger IntentRouter.route() or wait for observation data."
        ]

    recs: list[str] = []
    tiers = agg.get("tier_distribution", {})

    def _rate(tier: str) -> float:
        entry = tiers.get(tier, {})
        return float(entry.get("rate", 0)) if isinstance(entry, dict) else 0.0

    l1_rate = _rate("L1")
    l3_plus_fallback = _rate("L3") + _rate("fallback")

    # D1: L2 embedding worth the cost?
    if l3_plus_fallback > L3_FALLBACK_JUSTIFIES_L2:
        recs.append(
            f"D1 (embedding model): L3+fallback rate "
            f"{l3_plus_fallback * 100:.1f}% > {L3_FALLBACK_JUSTIFIES_L2 * 100:.0f}% "
            f"-> L2 embedding is JUSTIFIED."
        )
    else:
        recs.append(
            f"D1 (embedding model): L3+fallback rate "
            f"{l3_plus_fallback * 100:.1f}% <= {L3_FALLBACK_JUSTIFIES_L2 * 100:.0f}% "
            f"-> L2 embedding optional; reconsider Phase B priority."
        )

    # D4: load timing
    if l1_rate > L1_DOMINANT_FOR_LAZY:
        recs.append(
            f"D4 (load timing): L1 hit rate "
            f"{l1_rate * 100:.1f}% > {L1_DOMINANT_FOR_LAZY * 100:.0f}% "
            f"-> LAZY load embedding is safe (default stands)."
        )
    else:
        recs.append(
            f"D4 (load timing): L1 hit rate "
            f"{l1_rate * 100:.1f}% <= {L1_DOMINANT_FOR_LAZY * 100:.0f}% "
            f"-> consider EAGER load (L2 called on most queries)."
        )

    # Latency budget
    lat = agg.get("latency_ms", {})
    p95 = float(lat.get("p95", 0) or 0)
    if p95 < 50 - 20:  # 20 ms is the L2 embedding budget estimate
        recs.append(
            f"Latency: current p95 {p95}ms -> L2 (+~20ms) fits 50ms budget."
        )
    else:
        recs.append(
            f"Latency: current p95 {p95}ms -> L2 may breach 50ms budget, "
            f"consider ONNX-quantised embedding or cache prewarm."
        )

    return recs


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def format_report(agg: dict[str, Any], top_n: int = 5) -> str:
    lines: list[str] = []
    lines.append("=" * 72)
    lines.append("SuperOPC Routing Stats  |  Phase B Decision Support")
    lines.append("=" * 72)

    if agg.get("total_routes", 0) == 0:
        lines.append("No routing records found in the requested window.")
        lines.append("")
        for rec in phase_b_recommendations(agg):
            lines.append(f"  * {rec}")
        lines.append("=" * 72)
        return "\n".join(lines)

    dr = agg.get("date_range") or {}
    lines.append(f"Date range   : {dr.get('since', '?')} -> {dr.get('until', '?')}")
    lines.append(f"Total routes : {agg['total_routes']}")
    lines.append("")

    lines.append("-- Tier distribution --")
    for tier, info in agg["tier_distribution"].items():
        lines.append(
            f"  {tier:10s}: {info['count']:6d}  ({info['rate'] * 100:5.1f}%)"
        )
    lines.append("")

    lines.append("-- Latency (ms) --")
    for key, val in agg["latency_ms"].items():
        lines.append(f"  {key:5s}: {val}")
    lines.append("")

    lines.append(f"-- Top {top_n} skills (fallback excluded) --")
    if not agg["top_skills"]:
        lines.append("  (none)")
    for entry in agg["top_skills"]:
        lines.append(
            f"  {entry['skill_id']:30s} {entry['count']:6d}  "
            f"({entry['rate'] * 100:5.1f}%)"
        )
    lines.append("")

    lines.append("-- Miss analysis --")
    ma = agg["miss_analysis"]
    lines.append(
        f"  low_confidence  (<{LOW_CONFIDENCE_CUTOFF}): "
        f"{ma['low_confidence_count']:6d}  ({ma['low_confidence_rate'] * 100:5.1f}%)"
    )
    lines.append(
        f"  L3-rescued (useful)    : "
        f"{ma['l3_rescued_count']:6d}  ({ma['l3_rescued_rate'] * 100:5.1f}%)"
    )
    lines.append(
        f"  fallback -> using-sop  : "
        f"{ma['fallback_count']:6d}  ({ma['fallback_rate'] * 100:5.1f}%)"
    )
    lines.append("")

    lines.append("-- Phase B recommendations --")
    for rec in phase_b_recommendations(agg):
        lines.append(f"  * {rec}")
    lines.append("=" * 72)
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="opc_routing_stats",
        description=(
            "Aggregate .opc/routing/*.jsonl to support Phase B D1/D4 decisions."
        ),
    )
    parser.add_argument(
        "--days", type=int, default=30,
        help="scan the last N days (default: 30); overridden by --since",
    )
    parser.add_argument("--since", help="inclusive ISO date, e.g. 2026-04-21")
    parser.add_argument("--until", help="inclusive ISO date, e.g. 2026-05-05")
    parser.add_argument(
        "--routing-dir",
        default=os.environ.get("OPC_ROUTING_DIR", str(DEFAULT_ROUTING_DIR)),
        help=(
            "directory containing YYYY-MM-DD.jsonl files "
            "(env OPC_ROUTING_DIR overrides default)"
        ),
    )
    parser.add_argument("--top", type=int, default=5, help="top-N skills (default: 5)")
    parser.add_argument(
        "--json", action="store_true",
        help="emit machine-readable JSON instead of a text report",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)

    try:
        since = (
            date.fromisoformat(args.since)
            if args.since
            else date.today() - timedelta(days=max(args.days, 1) - 1)
        )
        until = date.fromisoformat(args.until) if args.until else date.today()
    except ValueError as exc:
        sys.stderr.write(f"invalid date: {exc}\n")
        return 2

    if since > until:
        sys.stderr.write(
            f"--since ({since}) must be <= --until ({until})\n"
        )
        return 2

    routing_dir = Path(args.routing_dir)
    records = list(iter_records(routing_dir, since=since, until=until))
    agg = aggregate(records, top_n=max(args.top, 1))

    if args.json:
        sys.stdout.write(
            json.dumps(agg, ensure_ascii=False, indent=2, sort_keys=False) + "\n"
        )
    else:
        sys.stdout.write(format_report(agg, top_n=max(args.top, 1)) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
