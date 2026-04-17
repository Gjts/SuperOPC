# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

> **Note:** SuperOPC v2 supports **dynamic context assembly**. For runtime-generated
> instructions tailored to the current project phase and developer profile, see
> `scripts/engine/context_assembler.py` which can produce a phase-aware CLAUDE.md
> dynamically.

## What this repository is

SuperOPC is a **content/plugin repository** with a **Python engine layer**, not a standalone application service. The main deliverables are:
- markdown-based **skills** in `skills/`
- markdown-based **agents** in `agents/` with capability registry `agents/registry.json`
- slash-command entrypoints in `commands/opc/`
- quality gates in `hooks/hooks.json` + `scripts/hooks/*.py`
- reusable engineering rules in `rules/`
- reference docs in `references/`
- format export tooling in `scripts/convert.py`
- **v2 engine layer** in `scripts/engine/` — event bus, state engine, DAG orchestrator, decision engine, cruise controller, profile engine, learning store, context assembler, notification dispatcher, and scheduler

Most changes in this repo are documentation and workflow changes; the main executable code is the hook scripts, the format converter, and the v2 engine modules.

## Core repository guidance

- Treat this repo as a **one-person company operating system** for solo founders: product, engineering, business, and market-intelligence workflows live side by side.
- Existing repo guidance is **skill-first**: if a relevant skill exists, prefer the skill-driven workflow over ad-hoc behavior.
- [!!CRITICAL RED FLAG!!] **Anti-Build-Trap Guardrail (Minimalist Entrepreneur):** Before executing any code generation or `brainstorming` for a new product/feature idea, you MUST force the user through the `validate-idea` and `find-community` skills. If there is no real-world proof of a paying community or validated niche, halt coding operations immediately and run `/opc-discuss`.
- Feature work follows the documented pipeline: `brainstorming -> planning -> implementing -> reviewing -> shipping`.
- Bug work follows: `debugging -> tdd -> implementing`.
- TDD is a repo-level expectation for behavior-changing work; `rules/common/testing.md` sets an **80% coverage target** and documents the RED/GREEN/REFACTOR loop.
- Commits are expected to use **Conventional Commits**; `rules/common/git-workflow.md` also forbids bypassing hooks with `--no-verify`.
- `AGENTS.md` instructs Claude to delegate proactively to specialist agents via `dag_engine.py` (v2) for planning, execution, review, verification, debugging, security review, and documentation.

## Common commands

### Install / use as a Claude Code plugin
```bash
git clone https://github.com/gjts/superopc.git
```

This repo is the **plugin source repository** for SuperOPC.

It is not yet published in a Claude Code-discoverable marketplace, so do **not** claim that users can install it with:
```text
/plugin install superopc
```

When the separate marketplace repository is live and verified, the expected end-user flow will be:
```text
/plugin marketplace add gjts/superopc-marketplace
/plugin install superopc@superopc-marketplace
```

### Generate integrations for other tools
```bash
python scripts/convert.py --tool cursor
python scripts/convert.py --tool windsurf
python scripts/convert.py --tool gemini-cli
python scripts/convert.py --tool opencode
python scripts/convert.py --tool openclaw
python scripts/convert.py --tool all
python scripts/convert.py --help
```

### Development reality for this repo

- `Python 3.11+` is required for `scripts/convert.py`, `scripts/opc_*.py`, and the hook scripts (`CONTRIBUTING.md`).
- There is currently **no repo-root `package.json`, Makefile, or dedicated build/lint/test script** for this repository itself.
- There is therefore **no repo-specific single-test command** to document right now.
- Validation is mainly done by checking:
  - markdown/frontmatter correctness
  - plugin manifest wiring
  - hook registration in `hooks/hooks.json`
  - repo / project health checks via `scripts/opc_quality.py` and `scripts/opc_health.py`
  - generated output under `integrations/` when converter behavior or source content changes

## High-level architecture

### 0. Engine layer (v2) — the autonomous nervous system
`scripts/engine/` is the new runtime core that turns SuperOPC from a passive prompt collection into an active system:

| Module | Purpose |
|--------|---------|
| `event_bus.py` | Publish/subscribe event bus — all internal communication goes through here |
| `state_engine.py` | Structured `.opc/` state with JSON+MD dual-write and event emission |
| `dag_engine.py` | DAG orchestrator v2 — resilient wave execution with retry/degrade/escalate |
| `decision_engine.py` | Three-layer brain: rule engine → state machine → ICE heuristics |
| `cruise_controller.py` | Autonomous operation with watch/assist/cruise modes |
| `scheduler.py` | Background cron for health checks, intel refresh, session recovery |
| `profile_engine.py` | 8-dimension developer profiling across sessions |
| `learning_store.py` | Cross-project knowledge persistence at `~/.opc/learnings/` |
| `context_assembler.py` | Dynamic context construction — phase-aware skill/agent/rule selection |
| `notification.py` | Multi-channel alerts: file, webhook, desktop, email |

Data flow: `Perception (events) → EventBus → DecisionEngine → DAGEngine → Agents → QualityGate → StateEngine → EventBus (loop)`

### 1. Commands are the user-facing entrypoints
`commands/opc/*.md` defines the top-level slash commands including `/opc-plan`, `/opc-build`, `/opc-ship`, `/opc-cruise`, `/opc-heartbeat`, `/opc-profile`, `/opc-intel`, and 20+ others.

These files are thin workflow routers. They do not contain the full logic themselves; instead they point Claude into the appropriate skill sequence.

### 2. Skills are the discovery + atomic-technique layer (v1.3 dispatcher pattern)

Starting in v1.3, SuperOPC adopts a **skill-dispatcher / agent-workflow** architecture. Skills are split into two kinds:

**Dispatcher skills** (≤ 30 lines each) — auto-trigger entries that delegate to an agent. They own the `description` that Claude's auto-discovery matches, and their job is to `Task()` the corresponding agent. They do NOT contain workflow steps, review rubrics, or templates.

- `skills/product/brainstorming/` → dispatches `opc-planner` Phase 0-1
- `skills/product/planning/` → dispatches `opc-planner` (full workflow)
- `skills/product/implementing/` → dispatches `opc-executor`
- `skills/product/reviewing/` → dispatches `opc-reviewer`
- `skills/product/shipping/` → dispatches `opc-shipper`
- `skills/using-superopc/workflow-modes/` → dispatches `opc-orchestrator` for 7-mode routing

**Atomic skills** — self-contained reusable techniques invoked from within agents:

- `skills/engineering/tdd/` — RED-GREEN-REFACTOR discipline
- `skills/engineering/agent-dispatch/` — subagent dispatch with 2 modes (serial+review / wave parallel), merged from the former `parallel-agents` and `subagent-driven-development` skills
- `skills/engineering/verification-loop/` — 4-layer verification + Nyquist sampling
- `skills/engineering/debugging/` — hypothesis/evidence/elimination cycle
- `skills/engineering/*-patterns/` — language/framework references
- `skills/business/**` — solo-founder playbooks (validation, pricing, finance, legal, GTM, content, interviews)
- `skills/intelligence/**` — market research, builder tracking, autonomous operations
- `skills/learning/**` — learning/evolution workflows
- `skills/using-superopc/SKILL.md` — meta-skill that bootstraps the whole system

When understanding SuperOPC behaviour: for a **business activity** (plan/build/review/ship), the authoritative source is the **agent** file. For an **atomic technique** (TDD, dispatch, verification), the authoritative source is the **atomic skill**.

### 3. Agents are the workflow owners

`agents/` contains 17 specialist roles. Under the v1.3 dispatcher pattern, **each agent is the single source of truth for its workflow** — planner owns planning flow, executor owns implementation flow, reviewer owns review flow, shipper owns release flow.

`agents/registry.json` provides a capability-based routing registry that the DAG engine uses for semantic task-to-agent matching (replacing the v1 keyword-based routing). `AGENTS.md` defines the intended orchestration patterns, including the main product pipeline (brainstorming → planning → implementing → reviewing → shipping) plus dedicated debugging, security-review, and autonomous-operation flows.

### 4. Rules and references are the quality system
- `rules/common/` applies across the repo
- `rules/typescript/` is the language-specific layer for `.ts` / `.tsx`
- `rules/csharp/` is the language-specific layer for `.cs`
- `references/` contains the supporting docs for gates, verification patterns, anti-patterns, TDD, git integration, and context budgeting

When changing implementation guidance or quality expectations, update the matching `rules/` or `references/` doc rather than scattering the same policy across many skills.

### 5. Hooks enforce guardrails around Claude tool use
`hooks/hooks.json` registers Claude Code hooks, and `scripts/hooks/*.py` contains the implementations.

Current hook coverage includes:
- blocking `git --no-verify`
- commit quality / secret scanning
- read-before-edit reminders
- config-protection warnings
- prompt-injection scanning for writes
- bash command audit logging
- console-log warnings after edits
- git-push reminders
- session summary persistence on stop

The repo docs describe these hooks as **advisory-first**: most warn rather than block, except for higher-severity checks.

### 6. `scripts/convert.py` republishes the repo to other ecosystems
`scripts/convert.py` is the main executable in the repo. It reads source content from:
- `skills/`
- `agents/`
- `commands/opc/`

…and writes derived artifacts to `integrations/<tool>/` for:
- Cursor
- Windsurf
- Gemini CLI
- OpenCode
- OpenClaw

`integrations/` should be treated as **generated output**, not the canonical source of truth.

### 7. Plugin metadata controls what Claude Code actually ships
- `.claude-plugin/plugin.json` is the plugin manifest used by Claude Code
- marketplace metadata for end-user installation should live in a **separate marketplace repository**, not in this plugin source repo

The plugin manifest should stay aligned with the full shipped agent set in `agents/`. If you add or rename an agent, update `.claude-plugin/plugin.json` in the same change.

## Workflow artifacts and expectations

- `/opc-plan` runs brainstorming + planning and outputs a `PLAN.md` artifact (the command docs refer to `docs/plans/`).
- `/opc-build` consumes a `PLAN.md`, executes tasks with TDD, and produces `SUMMARY.md`.
- `/opc-ship` verifies tests, summarizes changes, and handles merge / PR / keep / discard flows.
- `/opc-health` validates `.opc` integrity, requirements coverage, summary traceability, plugin / hook wiring, and internal markdown links.
- `/opc-quick` is the reduced-ceremony path: no formal `PLAN.md`, but it still keeps TDD and atomic-task execution.

If you are changing these workflows, make sure command docs, relevant skills, and agent expectations stay aligned.

## Editing guidance specific to this repo

- Prefer editing the **source-of-truth** files in `skills/`, `agents/`, `commands/`, `hooks/`, `rules/`, `references/`, and `scripts/`.
- Avoid hand-editing `integrations/` unless you are intentionally changing generated output or debugging the converter.
- Keep markdown frontmatter accurate; `name` and `description` are used by discovery/conversion flows.
- If you add or rename commands, agents, or skills, check whether `README.md`, `AGENTS.md`, `.claude-plugin/plugin.json`, or generated integrations also need updates.
- When editing repo policy, prefer updating the single authoritative location (for example `rules/common/testing.md` for testing policy or `hooks/hooks.json` for hook wiring) instead of duplicating the same rule in many places.

## SuperOPC Behavior Protocol (v2)

These rules are internalized from 9 upstream projects and enforced by the decision engine:

1. **[Superpowers] SKILL-FIRST** — If a relevant skill exists, invoke it, even with 1% applicability.
2. **[GSD] CONTEXT-DECAY-DEFENSE** — Monitor context budget; degrade gracefully at 80% usage.
3. **[ECC] CONTINUOUS-LEARNING** — After every session, capture insights to `~/.opc/learnings/`.
4. **[Minimalist Entrepreneur] ANTI-BUILD-TRAP** — No code generation without `validate-idea` + `find-community` evidence.
5. **[Superpowers] TDD-IRON-LAW** — No production code without a failing test first.
6. **[GSD] WAVE-EXECUTION** — Parallelize independent tasks; serialize dependent ones.
7. **[Agency-Agents] NEXUS-PROTOCOL** — Consult specialist agents for domain-specific work.
8. **[Follow Builders] BUILDER-INTEL** — Check builder feeds before market validation.
9. **[skill-from-masters] METHODOLOGY-FIRST** — Align with proven expert methodologies before creating new skills.
10. **[last30days] MULTI-SOURCE** — Use multiple data sources for market assessment.
11. **[Claude Code Best Practice] ATOMIC-COMMITS** — One task = one commit.

## Autonomous operations (v2)

SuperOPC can operate in three autonomous modes via `/opc-cruise`:
- **Watch**: Monitor only, alert on anomalies
- **Assist**: Execute GREEN zone tasks (health, tests, docs, intel), pause on YELLOW/RED
- **Cruise**: Execute GREEN + YELLOW tasks, pause only on RED zone (deploy, migrations, security, payments)

The decision engine (`scripts/engine/decision_engine.py`) determines actions through three layers:
1. Rule engine (deterministic patterns)
2. State machine (phase-aware flow)
3. ICE heuristics (prioritized scoring)

## Files worth reading first

- `README.md` — product positioning, install flow, and top-level architecture
- `AGENTS.md` — orchestration rules and specialist-agent usage
- `agents/registry.json` — capability-based agent routing registry
- `skills/using-superopc/SKILL.md` — meta-skill for how the system expects Claude to operate
- `skills/intelligence/autonomous-ops/SKILL.md` — autonomous operation permission zones
- `hooks/hooks.json` — actual hook registrations
- `rules/common/testing.md` and `rules/common/git-workflow.md` — repo-level quality and git expectations
- `scripts/engine/` — v2 engine layer (event bus, decision engine, cruise controller, etc.)
- `scripts/convert.py` — the multi-runtime export path
