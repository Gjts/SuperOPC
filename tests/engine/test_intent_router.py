"""Contract tests for scripts/engine/intent_router.py (Phase A Wave 1.3).

Authored BEFORE the router is implemented (TDD RED stage). After Wave 2.2 is
complete, these tests must go GREEN unchanged.

Contracts asserted:
  (a) L1 keyword hit >= L1_CONFIDENT_THRESHOLD returns path == ["L1"]
  (b) L1 miss falls through directly to L3 (Phase A skips L2)
  (c) Three-tier total miss returns skill_id == "using-superopc", confidence == 0
  (d) route() returns a structure with skill_id / confidence / path / latency_ms / candidates_explored
  (e) Each route() call appends a JSONL line under .opc/routing/YYYY-MM-DD.jsonl
  (f) Emits an event "skill.routed" on the default event bus
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def router_module():
    """Attempt to import the router. In RED stage this raises."""
    try:
        import intent_router  # type: ignore
    except ImportError as exc:
        pytest.fail(
            f"Cannot import intent_router: {exc}; Wave 2.2 not yet done."
        )
    return intent_router


@pytest.fixture
def isolated_router(tmp_path, monkeypatch, router_module):
    """Create an IntentRouter instance pointed at an isolated routing dir."""
    routing_dir = tmp_path / "routing"
    monkeypatch.setenv("OPC_ROUTING_DIR", str(routing_dir))
    # Many router constructors accept a `routing_dir` arg; try both APIs.
    try:
        r = router_module.IntentRouter(routing_dir=routing_dir)
    except TypeError:
        r = router_module.IntentRouter()
    return r, routing_dir


# ---------------------------------------------------------------------------
# Contract tests
# ---------------------------------------------------------------------------

def test_route_returns_required_structure(isolated_router):
    """(d) route() output has all mandatory keys."""
    router, _ = isolated_router
    result = router.route("规划登录功能")
    for key in ("skill_id", "confidence", "path", "latency_ms", "candidates_explored"):
        assert key in result, f"route() result missing key: {key}"
    assert isinstance(result["path"], list)
    assert isinstance(result["latency_ms"], (int, float))


def test_l1_keyword_hit_returns_planning(isolated_router):
    """(a) An explicit planning trigger must hit L1 and return planning skill."""
    router, _ = isolated_router
    result = router.route("帮我规划登录功能")
    assert result["skill_id"] == "planning", (
        f"expected planning, got {result['skill_id']}"
    )
    assert "L1" in result["path"], f"expected L1 in path, got {result['path']}"


def test_l1_miss_falls_through_to_l3(isolated_router, router_module):
    """(b) No-keyword input must escalate to L3 in Phase A (no L2)."""
    router, _ = isolated_router
    # Force L3 via a vague sentence with zero keyword overlap.
    result = router.route("xyzzy frobnicate quux")
    assert "L2" not in result["path"], (
        f"Phase A must NOT use L2; got path={result['path']}"
    )
    # Either L3 was consulted, or the three-tier fallback kicked in.
    assert "L3" in result["path"] or result["skill_id"] == "using-superopc"


def test_total_miss_falls_back_to_using_superopc(isolated_router, monkeypatch, router_module):
    """(c) When every tier misses, fallback is using-superopc with confidence 0."""
    router, _ = isolated_router

    # Force L3 to return a clear miss signal.
    def fake_l3(prompt, candidates):
        return {"skill_id": None, "confidence": 0.0}

    if hasattr(router_module, "_call_llm"):
        monkeypatch.setattr(router_module, "_call_llm", fake_l3)

    result = router.route("qqqqqqq wwwwwwwww")
    assert result["skill_id"] == "using-superopc"
    assert result["confidence"] == 0.0


def test_route_appends_jsonl_log(isolated_router):
    """(e) Every route() call appends one JSONL line to .opc/routing/<date>.jsonl."""
    router, routing_dir = isolated_router
    router.route("规划登录")
    router.route("请帮我实现登录")
    today = datetime.now().strftime("%Y-%m-%d")
    log_file = routing_dir / f"{today}.jsonl"
    assert log_file.exists(), f"routing log not created: {log_file}"
    lines = [line for line in log_file.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) >= 2, f"expected >=2 log lines, got {len(lines)}"
    # Every line must be valid JSON with an input_hash field.
    for line in lines:
        rec = json.loads(line)
        assert "input_hash" in rec, f"log line missing input_hash: {rec}"
        assert "skill_id" in rec
        assert "path" in rec


def test_route_emits_event(isolated_router, router_module):
    """(f) route() publishes a skill.routed event on the event bus."""
    from event_bus import EventBus, reset_event_bus
    reset_event_bus()
    received: list[object] = []
    from event_bus import get_event_bus
    bus = get_event_bus()
    bus.subscribe("skill.routed", lambda e: received.append(e))

    router, _ = isolated_router
    router.route("帮我规划登录")
    assert received, "no skill.routed event emitted"
    reset_event_bus()
