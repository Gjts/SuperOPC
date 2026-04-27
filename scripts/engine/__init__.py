"""
SuperOPC Engine v2 — Autonomous operations layer.

Runtime modules (loaded on demand via direct imports):
  event_bus          — Publish/subscribe event bus (core nervous system)
  state_engine       — Structured .opc/ state with JSON+MD dual-write
  dag_engine         — DAG orchestration with retry/degrade/escalate
  decision_engine    — Three-layer decision (rules / state-machine / ICE)
  cruise_controller  — Autonomous cruise modes (watch/assist/cruise) and
                       host-aware agent dispatch
  scheduler          — Background cron for health checks, intel refresh
  profile_engine     — 8-dimension developer profiling across sessions
  learning_store     — Cross-project knowledge persistence
  context_assembler  — Dynamic phase-aware CLAUDE.md assembly
  notification       — Multi-channel notification dispatcher
  intel_engine       — Codebase intelligence (queryable JSON index)
  instinct_generator — Observation-to-rule pipeline (closes learning loop)
  intent_router      — L1/L3 skill intent router (v1.4.1; L2 embedding in v1.5)

All modules are importable by short name when this package is on sys.path
(see tests/conftest.py).
"""
