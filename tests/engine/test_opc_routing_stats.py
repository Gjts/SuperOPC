"""Contract tests for scripts/opc_routing_stats.py (RED phase).

These tests lock down the aggregation contract so that Phase B decision
making (D1 embedding model, D4 load timing, latency budget) has a stable
data source.
"""

from __future__ import annotations

import json
import sys
from datetime import date
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import opc_routing_stats as ors  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _write_jsonl(path: Path, records: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as fh:
        for record in records:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")


@pytest.fixture()
def routing_dir(tmp_path: Path) -> Path:
    rd = tmp_path / "routing"
    rd.mkdir()
    _write_jsonl(
        rd / "2026-04-21.jsonl",
        [
            # L1 hit, high score
            {
                "ts": "2026-04-21T10:00:00",
                "input_hash": "a" * 16,
                "input_len": 10,
                "skill_id": "planning",
                "confidence": 0.5,
                "path": ["L1"],
                "latency_ms": 0.1,
                "candidates_explored": 17,
                "tier_scores": {"L1": 50.0},
            },
            # L1 hit, low score
            {
                "ts": "2026-04-21T10:01:00",
                "input_hash": "b" * 16,
                "input_len": 8,
                "skill_id": "debugging",
                "confidence": 0.2,
                "path": ["L1"],
                "latency_ms": 0.2,
                "candidates_explored": 17,
                "tier_scores": {"L1": 20.0},
            },
            # L3 rescued (not fallback)
            {
                "ts": "2026-04-21T10:02:00",
                "input_hash": "c" * 16,
                "input_len": 15,
                "skill_id": "shipping",
                "confidence": 0.7,
                "path": ["L1", "L3"],
                "latency_ms": 50.0,
                "candidates_explored": 5,
                "tier_scores": {"L1": 0.0, "L3": 0.7},
            },
            # Fallback (L3 gave up, landed on using-superopc)
            {
                "ts": "2026-04-21T10:03:00",
                "input_hash": "d" * 16,
                "input_len": 17,
                "skill_id": "using-superopc",
                "confidence": 0.0,
                "path": ["L1", "L3"],
                "latency_ms": 45.0,
                "candidates_explored": 5,
                "tier_scores": {"L1": 0.0, "L3": 0.0},
            },
        ],
    )
    _write_jsonl(
        rd / "2026-04-22.jsonl",
        [
            {
                "ts": "2026-04-22T09:00:00",
                "input_hash": "e" * 16,
                "input_len": 12,
                "skill_id": "planning",
                "confidence": 0.5,
                "path": ["L1"],
                "latency_ms": 0.15,
                "candidates_explored": 17,
                "tier_scores": {"L1": 50.0},
            },
        ],
    )
    return rd


# ---------------------------------------------------------------------------
# aggregate() contract
# ---------------------------------------------------------------------------


def test_aggregate_empty_records_returns_zero_total() -> None:
    agg = ors.aggregate([])
    assert agg["total_routes"] == 0
    assert agg["date_range"] is None
    assert agg["tier_distribution"] == {}
    assert agg["top_skills"] == []


def test_aggregate_tier_distribution_splits_l1_l3_fallback(
    routing_dir: Path,
) -> None:
    records = list(ors.iter_records(routing_dir, since=None, until=None))
    agg = ors.aggregate(records)

    tiers = agg["tier_distribution"]
    # Expected: 3 L1 (2 from day1 + 1 from day2), 1 L3, 1 fallback
    assert tiers["L1"]["count"] == 3
    assert tiers["L3"]["count"] == 1
    assert tiers["fallback"]["count"] == 1
    # Rates must sum to 1.0
    total_rate = sum(info["rate"] for info in tiers.values())
    assert abs(total_rate - 1.0) < 1e-9


def test_aggregate_latency_percentiles_sorted(routing_dir: Path) -> None:
    records = list(ors.iter_records(routing_dir, since=None, until=None))
    agg = ors.aggregate(records)
    lat = agg["latency_ms"]
    # latencies sorted: [0.1, 0.15, 0.2, 45.0, 50.0]
    assert lat["p50"] == pytest.approx(0.2, abs=0.01)
    assert lat["max"] == pytest.approx(50.0, abs=0.01)
    assert lat["avg"] == pytest.approx((0.1 + 0.15 + 0.2 + 45.0 + 50.0) / 5, abs=0.01)


def test_aggregate_top_skills_excludes_fallback(routing_dir: Path) -> None:
    records = list(ors.iter_records(routing_dir, since=None, until=None))
    agg = ors.aggregate(records, top_n=3)
    ids = [entry["skill_id"] for entry in agg["top_skills"]]
    # planning counts 2, then debugging and shipping count 1 each
    # using-superopc (fallback with confidence=0) MUST be excluded
    assert "using-superopc" not in ids
    assert ids[0] == "planning"
    assert agg["top_skills"][0]["count"] == 2


def test_aggregate_miss_analysis_separates_l3_rescue_from_fallback(
    routing_dir: Path,
) -> None:
    records = list(ors.iter_records(routing_dir, since=None, until=None))
    agg = ors.aggregate(records)
    ma = agg["miss_analysis"]
    # shipping was L3-rescued (skill != using-superopc, confidence > 0)
    assert ma["l3_rescued_count"] == 1
    # fallback is exactly 1 (the using-superopc row)
    assert ma["fallback_count"] == 1
    # low_confidence: debugging (0.2) is borderline; spec = strictly < 0.2
    #   so: only confidence=0.0 (fallback) counts
    assert ma["low_confidence_count"] >= 1


# ---------------------------------------------------------------------------
# iter_records() filtering
# ---------------------------------------------------------------------------


def test_iter_records_filters_by_since(routing_dir: Path) -> None:
    records = list(
        ors.iter_records(routing_dir, since=date(2026, 4, 22), until=None)
    )
    assert len(records) == 1
    assert records[0]["skill_id"] == "planning"


def test_iter_records_handles_missing_dir(tmp_path: Path) -> None:
    records = list(
        ors.iter_records(tmp_path / "nonexistent", since=None, until=None)
    )
    assert records == []


def test_iter_records_skips_malformed_lines(tmp_path: Path) -> None:
    rd = tmp_path / "routing"
    rd.mkdir()
    f = rd / "2026-04-21.jsonl"
    f.write_text(
        '{"skill_id": "planning", "path": ["L1"], "latency_ms": 0.1, "confidence": 0.5}\n'
        "not-json-garbage\n"
        '{"skill_id": "debugging", "path": ["L1"], "latency_ms": 0.2, "confidence": 0.2}\n',
        encoding="utf-8",
    )
    records = list(ors.iter_records(rd, since=None, until=None))
    assert len(records) == 2


# ---------------------------------------------------------------------------
# Phase B decision recommendations
# ---------------------------------------------------------------------------


def test_recommendations_flag_l2_justified_when_l3_high() -> None:
    agg = {
        "total_routes": 100,
        "tier_distribution": {
            "L1": {"count": 50, "rate": 0.50},
            "L3": {"count": 30, "rate": 0.30},
            "fallback": {"count": 20, "rate": 0.20},
        },
        "latency_ms": {"p95": 0.5},
    }
    recs = ors.phase_b_recommendations(agg)
    assert any("D1" in r and "justified" in r.lower() for r in recs)


def test_recommendations_flag_lazy_load_when_l1_dominant() -> None:
    agg = {
        "total_routes": 100,
        "tier_distribution": {
            "L1": {"count": 80, "rate": 0.80},
            "L3": {"count": 10, "rate": 0.10},
            "fallback": {"count": 10, "rate": 0.10},
        },
        "latency_ms": {"p95": 0.5},
    }
    recs = ors.phase_b_recommendations(agg)
    assert any("D4" in r and "lazy" in r.lower() for r in recs)


def test_recommendations_empty_data_gracefully() -> None:
    recs = ors.phase_b_recommendations({"total_routes": 0})
    assert len(recs) == 1
    assert "no routing records" in recs[0].lower()


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_cli_json_output_schema(
    routing_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    exit_code = ors.main([
        "--routing-dir", str(routing_dir),
        "--since", "2026-04-21",
        "--until", "2026-04-22",
        "--json",
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    payload = json.loads(out)
    assert set(payload.keys()) >= {
        "total_routes",
        "date_range",
        "tier_distribution",
        "latency_ms",
        "top_skills",
        "miss_analysis",
    }


def test_cli_text_output_human_readable(
    routing_dir: Path, capsys: pytest.CaptureFixture
) -> None:
    exit_code = ors.main([
        "--routing-dir", str(routing_dir),
        "--since", "2026-04-21",
        "--until", "2026-04-22",
    ])
    assert exit_code == 0
    out = capsys.readouterr().out
    assert "SuperOPC Routing Stats" in out
    assert "Tier distribution" in out
    assert "Phase B recommendations" in out
