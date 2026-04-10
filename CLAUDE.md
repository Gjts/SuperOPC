# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this repository is

SuperOPC is a **content/plugin repository**, not an application service. The main deliverables are Claude Code instructions and workflow assets:
- markdown-based **skills** in `skills/`
- markdown-based **agents** in `agents/`
- slash-command entrypoints in `commands/opc/`
- quality gates in `hooks/hooks.json` + `scripts/hooks/*.js`
- reusable engineering rules in `rules/`
- reference docs in `references/`
- format export tooling in `scripts/convert.js`

Most changes in this repo are documentation and workflow changes; the main executable code is the hook scripts and the format converter.

## Core repository guidance

- Treat this repo as a **one-person company operating system** for solo founders: product, engineering, business, and market-intelligence workflows live side by side.
- Existing repo guidance is **skill-first**: if a relevant skill exists, prefer the skill-driven workflow over ad-hoc behavior.
- Feature work follows the documented pipeline: `brainstorming -> planning -> implementing -> reviewing -> shipping`.
- Bug work follows: `debugging -> tdd -> implementing`.
- TDD is a repo-level expectation for behavior-changing work; `rules/common/testing.md` sets an **80% coverage target** and documents the RED/GREEN/REFACTOR loop.
- Commits are expected to use **Conventional Commits**; `rules/common/git-workflow.md` also forbids bypassing hooks with `--no-verify`.
- `AGENTS.md` instructs Claude to delegate proactively to specialist agents for planning, execution, review, verification, debugging, security review, and documentation.

## Common commands

### Install / use as a Claude Code plugin
```bash
git clone https://github.com/gjts/superopc.git ~/.claude/plugins/superopc
```

Then inside Claude Code:
```text
/plugin install superopc
```

Marketplace metadata also advertises:
```text
/plugin marketplace add gjts/superopc
```

### Generate integrations for other tools
```bash
node scripts/convert.js --tool cursor
node scripts/convert.js --tool windsurf
node scripts/convert.js --tool gemini-cli
node scripts/convert.js --tool opencode
node scripts/convert.js --tool openclaw
node scripts/convert.js --tool all
node scripts/convert.js --help
```

### Development reality for this repo

- `Node.js 18+` is required for `scripts/convert.js` and the hook scripts (`CONTRIBUTING.md`).
- There is currently **no repo-root `package.json`, Makefile, or dedicated build/lint/test script** for this repository itself.
- There is therefore **no repo-specific single-test command** to document right now.
- Validation is mainly done by checking:
  - markdown/frontmatter correctness
  - plugin manifest wiring
  - hook registration in `hooks/hooks.json`
  - generated output under `integrations/` when converter behavior or source content changes

## High-level architecture

### 1. Commands are the user-facing entrypoints
`commands/opc/*.md` defines the top-level slash commands such as `/opc-plan`, `/opc-build`, `/opc-ship`, `/opc-quick`, `/opc-review`, and `/opc-research`.

These files are thin workflow routers. They do not contain the full logic themselves; instead they point Claude into the appropriate skill sequence.

### 2. Skills are the main behavior layer
`skills/` is the core of the system and is organized by operating domain:
- `skills/product/` — product delivery pipeline
- `skills/engineering/` — TDD, debugging, git worktrees, parallel execution
- `skills/business/` — solo-founder operating skills
- `skills/intelligence/` — market research and builder tracking
- `skills/learning/` — learning/evolution workflows
- `skills/using-superopc/` — meta-skill that explains how the whole system should be used

If you need to understand how SuperOPC is supposed to behave, start with the relevant skill before reading individual agents.

### 3. Agents are specialist delegates
`agents/` contains the specialist roles used by the workflows: planner, executor, reviewer, researcher, verifier, debugger, security auditor, documentation roles, UI/codebase analysis roles, and roadmap/planning roles.

`AGENTS.md` defines the intended orchestration patterns, e.g. planner -> executor -> reviewer -> verifier, plus dedicated debugging and security-review flows.

### 4. Rules and references are the quality system
- `rules/common/` applies across the repo
- `rules/typescript/` is the language-specific layer for `.ts` / `.tsx`
- `rules/csharp/` is the language-specific layer for `.cs`
- `references/` contains the supporting docs for gates, verification patterns, anti-patterns, TDD, git integration, and context budgeting

When changing implementation guidance or quality expectations, update the matching `rules/` or `references/` doc rather than scattering the same policy across many skills.

### 5. Hooks enforce guardrails around Claude tool use
`hooks/hooks.json` registers Claude Code hooks, and `scripts/hooks/*.js` contains the implementations.

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

### 6. `scripts/convert.js` republishes the repo to other ecosystems
`scripts/convert.js` is the main executable in the repo. It reads source content from:
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
- `.claude-plugin/marketplace.json` contains marketplace metadata

Important detail: the repo contains more agent definitions in `agents/` than are currently registered in `.claude-plugin/plugin.json`. If you expect a new or edited agent to be available through the shipped plugin, update the manifest as well as the markdown file.

## Workflow artifacts and expectations

- `/opc-plan` runs brainstorming + planning and outputs a `PLAN.md` artifact (the command docs refer to `docs/plans/`).
- `/opc-build` consumes a `PLAN.md`, executes tasks with TDD, and produces `SUMMARY.md`.
- `/opc-ship` verifies tests, summarizes changes, and handles merge / PR / keep / discard flows.
- `/opc-quick` is the reduced-ceremony path: no formal `PLAN.md`, but it still keeps TDD and atomic-task execution.

If you are changing these workflows, make sure command docs, relevant skills, and agent expectations stay aligned.

## Editing guidance specific to this repo

- Prefer editing the **source-of-truth** files in `skills/`, `agents/`, `commands/`, `hooks/`, `rules/`, `references/`, and `scripts/`.
- Avoid hand-editing `integrations/` unless you are intentionally changing generated output or debugging the converter.
- Keep markdown frontmatter accurate; `name` and `description` are used by discovery/conversion flows.
- If you add or rename commands, agents, or skills, check whether `README.md`, `AGENTS.md`, `.claude-plugin/plugin.json`, or generated integrations also need updates.
- When editing repo policy, prefer updating the single authoritative location (for example `rules/common/testing.md` for testing policy or `hooks/hooks.json` for hook wiring) instead of duplicating the same rule in many places.

## Files worth reading first

- `README.md` — product positioning, install flow, and top-level architecture
- `AGENTS.md` — orchestration rules and specialist-agent usage
- `skills/using-superopc/SKILL.md` — meta-skill for how the system expects Claude to operate
- `hooks/hooks.json` — actual hook registrations
- `rules/common/testing.md` and `rules/common/git-workflow.md` — repo-level quality and git expectations
- `scripts/convert.js` — the main executable path in the repo
