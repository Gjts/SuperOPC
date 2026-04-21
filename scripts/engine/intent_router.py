#!/usr/bin/env python3
"""
intent_router.py — Three-tier skill intent router (Phase A: L1 + L3).

Given a natural-language input, determine which SuperOPC skill to invoke
before the AI consumes the full system prompt. Routes are audit-logged to
.opc/routing/YYYY-MM-DD.jsonl and announced on the event bus as
`skill.routed`.

Tiers:
    L1  Rule-based keyword + phrase scoring over skills/registry.json
        triggers. Fast, deterministic, free.
    L2  (skipped in Phase A — reserved for local embedding retrieval)
    L3  Small LLM fallback (`_call_llm`). In Phase A this is a mock that
        returns no-match; production integration lands in Phase B.

If all tiers miss, `using-superopc` is returned with confidence 0 so the
skill-first bootstrap still runs.

Design: docs/adr/0002-intent-router-tiers.md
Tests:  tests/engine/test_intent_router.py
"""
from __future__ import annotations

import hashlib
import json
import os
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

# conftest.py puts scripts/engine on sys.path, so bare imports work in tests.
from event_bus import get_event_bus  # type: ignore

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_REGISTRY = REPO_ROOT / "skills" / "registry.json"
DEFAULT_ROUTING_DIR = REPO_ROOT / ".opc" / "routing"

L1_CONFIDENT_THRESHOLD = 20
FALLBACK_SKILL_ID = "using-superopc"


# ---------------------------------------------------------------------------
# Tier 3 LLM placeholder
# ---------------------------------------------------------------------------

def _call_llm(prompt: str, candidates: list[dict[str, Any]]) -> dict[str, Any]:
    """Phase A mock — deterministic "no confident match" response.

    Tests monkey-patch this symbol. Phase B will replace the body with a
    real LLM call (OpenRouter / local model). Signature and return shape
    are the stable contract.

    Returns:
        {"skill_id": str | None, "confidence": float in [0, 1]}
        skill_id=None means the LLM could not pick a confident candidate.
    """
    # No-op mock: always returns a miss. A real LLM call would inspect the
    # candidate list and pick the best-fit id.
    return {"skill_id": None, "confidence": 0.0}


# ---------------------------------------------------------------------------
# Data shapes
# ---------------------------------------------------------------------------

@dataclass
class RouteResult:
    skill_id: str
    confidence: float
    path: list[str]
    latency_ms: float
    candidates_explored: int
    tier_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "skill_id": self.skill_id,
            "confidence": self.confidence,
            "path": list(self.path),
            "latency_ms": round(self.latency_ms, 3),
            "candidates_explored": self.candidates_explored,
            "tier_scores": dict(self.tier_scores),
        }


# ---------------------------------------------------------------------------
# Router
# ---------------------------------------------------------------------------

class IntentRouter:
    """Picks the most relevant SuperOPC skill for a given user input."""

    def __init__(
        self,
        registry_path: Path | None = None,
        routing_dir: Path | None = None,
    ) -> None:
        self.registry_path = Path(registry_path) if registry_path else DEFAULT_REGISTRY
        env_dir = os.environ.get("OPC_ROUTING_DIR")
        if routing_dir is not None:
            self.routing_dir = Path(routing_dir)
        elif env_dir:
            self.routing_dir = Path(env_dir)
        else:
            self.routing_dir = DEFAULT_ROUTING_DIR
        self._skills: list[dict[str, Any]] = self._load_skills()

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------
    def route(self, user_input: str) -> dict[str, Any]:
        start = time.perf_counter()
        path: list[str] = []
        tier_scores: dict[str, float] = {}

        # ---- L1 ----------------------------------------------------------
        l1_hit, l1_score = self._try_l1(user_input)
        path.append("L1")
        tier_scores["L1"] = l1_score
        if l1_hit is not None and l1_score >= L1_CONFIDENT_THRESHOLD:
            result = RouteResult(
                skill_id=l1_hit["id"],
                confidence=min(1.0, l1_score / 100.0),
                path=path,
                latency_ms=(time.perf_counter() - start) * 1000,
                candidates_explored=len(self._skills),
                tier_scores=tier_scores,
            )
            self._finalize(user_input, result)
            return result.to_dict()

        # ---- L2 (skipped in Phase A) ------------------------------------
        # Intentionally left blank: path will not include "L2".

        # ---- L3 ----------------------------------------------------------
        path.append("L3")
        l3 = _call_llm(user_input, self._shortlist(l1_score_hints=tier_scores["L1"]))
        tier_scores["L3"] = float(l3.get("confidence") or 0.0)
        chosen_id = l3.get("skill_id")
        chosen = self._lookup(chosen_id) if chosen_id else None
        if chosen:
            result = RouteResult(
                skill_id=chosen["id"],
                confidence=float(l3.get("confidence") or 0.0),
                path=path,
                latency_ms=(time.perf_counter() - start) * 1000,
                candidates_explored=len(self._skills),
                tier_scores=tier_scores,
            )
            self._finalize(user_input, result)
            return result.to_dict()

        # ---- Fallback ----------------------------------------------------
        result = RouteResult(
            skill_id=FALLBACK_SKILL_ID,
            confidence=0.0,
            path=path,
            latency_ms=(time.perf_counter() - start) * 1000,
            candidates_explored=len(self._skills),
            tier_scores=tier_scores,
        )
        self._finalize(user_input, result)
        return result.to_dict()

    # ------------------------------------------------------------------
    # Tier implementations
    # ------------------------------------------------------------------
    def _try_l1(self, text: str) -> tuple[dict[str, Any] | None, float]:
        """Return (best_skill, best_score). best_skill is None on empty match."""
        text_l = text.lower()
        best: dict[str, Any] | None = None
        best_score = 0.0
        for skill in self._skills:
            if skill.get("id") == FALLBACK_SKILL_ID:
                # Never let the fallback meta skill win L1 on its own.
                continue
            score = self._score_skill(text_l, skill.get("triggers") or {})
            if score > best_score:
                best_score = score
                best = skill
        return best, best_score

    @staticmethod
    def _score_skill(text_l: str, triggers: dict[str, Any]) -> float:
        score = 0.0
        for kw in triggers.get("keywords") or []:
            if isinstance(kw, str) and kw.strip() and kw.lower() in text_l:
                score += 20
        for phrase in triggers.get("phrases") or []:
            if isinstance(phrase, str) and phrase.strip() and phrase.lower() in text_l:
                score += 30
        return score

    def _shortlist(self, l1_score_hints: float, k: int = 5) -> list[dict[str, Any]]:
        # For Phase A the LLM sees a compact shortlist (dispatcher types first).
        ranked = sorted(
            self._skills,
            key=lambda s: (
                0 if s.get("type") == "dispatcher" else 1,
                s.get("id", ""),
            ),
        )
        return [
            {"id": s["id"], "description": s.get("description", "")[:160]}
            for s in ranked[:k]
        ]

    def _lookup(self, skill_id: str) -> dict[str, Any] | None:
        for s in self._skills:
            if s.get("id") == skill_id:
                return s
        return None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------
    def _finalize(self, user_input: str, result: RouteResult) -> None:
        self._log(user_input, result)
        self._emit(user_input, result)

    def _log(self, user_input: str, result: RouteResult) -> None:
        self.routing_dir.mkdir(parents=True, exist_ok=True)
        date_key = datetime.now().strftime("%Y-%m-%d")
        log_file = self.routing_dir / f"{date_key}.jsonl"
        record = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            "input_hash": hashlib.sha256(user_input.encode("utf-8")).hexdigest()[:16],
            "input_len": len(user_input),
            **result.to_dict(),
        }
        with log_file.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record, ensure_ascii=False) + "\n")

    @staticmethod
    def _emit(user_input: str, result: RouteResult) -> None:
        try:
            bus = get_event_bus()
            bus.publish(
                "skill.routed",
                {
                    "skill_id": result.skill_id,
                    "confidence": result.confidence,
                    "path": list(result.path),
                    "latency_ms": round(result.latency_ms, 3),
                    "input_hash": hashlib.sha256(user_input.encode("utf-8")).hexdigest()[:16],
                },
                source="intent_router",
            )
        except Exception:
            # Never let observability break routing.
            pass

    # ------------------------------------------------------------------
    # Registry loading
    # ------------------------------------------------------------------
    def _load_skills(self) -> list[dict[str, Any]]:
        if not self.registry_path.exists():
            return []
        data = json.loads(self.registry_path.read_text(encoding="utf-8"))
        skills = data.get("skills", [])
        if not isinstance(skills, list):
            return []
        return [s for s in skills if isinstance(s, dict) and s.get("id")]


# ---------------------------------------------------------------------------
# CLI smoke helper
# ---------------------------------------------------------------------------

def _main() -> None:
    import argparse, sys

    parser = argparse.ArgumentParser(description="Route input through IntentRouter")
    parser.add_argument("input", nargs="+", help="free-form user input")
    parser.add_argument("--registry", default=None)
    args = parser.parse_args()
    router = IntentRouter(registry_path=args.registry)
    result = router.route(" ".join(args.input))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")


if __name__ == "__main__":
    _main()
