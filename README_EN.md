<div align="center">

# SuperOPC

**The One-Person Company Operating System**

AI-powered workflows, agents, and skills to help solo founders build, ship, and grow products.

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[中文](README.md) · **English**

</div>

---

## Why SuperOPC?

Solo founders wear every hat — CEO, CTO, designer, marketer, support. You don't need enterprise tools built for 50-person teams. You need **one super-tool** that unifies all these roles into a single system.

SuperOPC merges the best AI engineering practices from the open-source community:

| Source | Contribution |
|--------|-------------|
| [Superpowers](https://github.com/obra/superpowers) | Skill system, TDD discipline, systematic debugging, Git worktrees |
| [Get Shit Done](https://github.com/gsd-build/get-shit-done) | Command system, wave execution, agent orchestration, verifier |
| [Minimalist Entrepreneur Skills](https://github.com/slavingia/skills) | 10 lean startup skills |
| [last30days](https://github.com/zarazhangrui/last30days-skill) | Multi-source market research |
| [Follow Builders](https://github.com/zarazhangrui/follow-builders) | Builder intelligence tracking |
| [Everything Claude Code](https://github.com/nicobailon/everything-claude-code) | Install system, continuous learning, agent delegation |
| [skill-from-masters](https://github.com/zarazhangrui/skill-from-masters) | Learn-from-experts methodology |
| [agency-agents](https://github.com/agency-agents/agency-agents) | Professional AI agent definitions |
| [Claude Code Best Practice](https://github.com/anthropics/claude-code-best-practice) | Workflow orchestration, hooks system |

## Installation

### Claude Code

```bash
git clone https://github.com/gjts/superopc.git ~/.claude/plugins/superopc
```

Then in Claude Code:
```
/plugin install superopc
```

### Multi-Runtime Export (11 targets)

```bash
git clone https://github.com/gjts/superopc.git
cd superopc
python scripts/convert.py --tool claude-code  # Export native Claude Code package
python scripts/convert.py --tool cursor       # Generate Cursor rules
python scripts/convert.py --tool copilot      # Generate GitHub Copilot instructions
python scripts/convert.py --tool codex        # Generate Codex agents/commands/skills
python scripts/convert.py --tool all          # Generate all exports at once
python scripts/convert.py --tool auto         # Auto-detect runtime from environment
```

Supported runtimes: **Claude Code**, **Cursor**, **Windsurf**, **Copilot**, **Gemini CLI**, **OpenCode**, **Codex**, **Trae**, **Cline**, **Augment Code**, **OpenClaw**.

Converted files output to `integrations/<tool>/`. The converter provides:
- **Runtime registry** — unified directory, frontmatter, and output layout per target
- **Tool name mapping** — translates Claude Code tool names to target runtime equivalents
- **Hook event mapping** — generates `HOOKS.md` + `runtime-map.json` per export
- **Auto-detection** — `--tool auto` / `--detect` suggests export targets from config files

### MCP Server Templates

SuperOPC ships with reusable MCP templates in `mcp-configs/mcp-servers.json`:
- `context7` — real-time documentation queries
- `supabase` — Supabase database / project operations
- `sequential-thinking` — step-by-step reasoning
- `playwright` — browser automation / E2E verification

Copy the entries you need into your runtime's MCP config and replace placeholders.

## Hooks System

Built-in quality gate hooks (based on [ECC hooks.json](https://github.com/nicobailon/everything-claude-code) patterns):

| Hook | Type | Function |
|------|------|----------|
| **block-no-verify** | PreToolUse | Block `git --no-verify` bypass |
| **commit-quality** | PreToolUse | Conventional Commits format + secret scanning |
| **read-before-edit** | PreToolUse | Remind to read before editing (advisory) |
| **config-protection** | PreToolUse | Protect linter/formatter configs |
| **prompt-injection-scan** | PreToolUse | Scan for common prompt injection patterns |
| **command-audit-log** | PostToolUse | Audit log to `.opc/audit.log` |
| **console-log-warn** | PostToolUse | Detect debug statements, remind cleanup |
| **session-summary** | Stop | Persist basic session summary |

Hooks follow the **advisory-first principle** — most hooks warn rather than block.

## Architecture

```
SuperOPC/
├── skills/                    # Skill system (core)
│   ├── using-superopc/        # Meta-skills: how to use the system
│   ├── product/               # Product development (5 skills)
│   ├── engineering/           # Engineering quality (19 skills)
│   ├── business/              # Business operations (18 skills)
│   ├── intelligence/          # Market intelligence (2 skills)
│   └── learning/              # Learning & evolution (3 skills)
├── agents/                    # Professional agents (15)
├── commands/opc/              # Slash commands (23)
├── hooks/                     # Quality gate hooks
├── rules/                     # Coding rules (4 languages)
├── references/                # Reference documents
├── templates/                 # .opc templates + project templates
│   └── projects/              # Starter templates (4 types)
├── examples/                  # Usage examples (3 walkthroughs)
├── scripts/                   # Tool scripts
├── mcp-configs/               # MCP server templates
├── integrations/              # Generated runtime exports (11 targets)
└── tests/                     # Quality tests
```

## Quick Start

### 1. Initialize a project
```
/opc-start
```
Answer a few questions, SuperOPC creates the project structure.

### 2. Plan a feature
```
/opc-plan user login system
```
AI designs 2-3 approaches → you pick one → generates implementation plan.

### 3. Build
```
/opc-build
```
AI executes task-by-task TDD → two-stage review → atomic commits.

### 4. Ship
```
/opc-ship
```
Run tests → merge/PR → cleanup.

### 5. Business decisions
```
/opc-research AI writing tools market
```
Multi-source research → competitive analysis → action recommendations.

### 6. View dashboard
```bash
python scripts/opc_dashboard.py --cwd /path/to/your/project
```

### 7. Pause and resume
```bash
python scripts/opc_pause.py --cwd . --note "stopping here for today"
python scripts/opc_resume.py --cwd .
```

### 8. Health check
```bash
python scripts/opc_health.py --cwd . --repair
```

## Project Templates

SuperOPC includes 4 starter templates in `templates/projects/`:

| Template | Stack | Use Case |
|----------|-------|----------|
| **saas-starter** | Next.js 14 + Supabase + Stripe | SaaS MVP, subscription products |
| **api-service** | .NET 8 + PostgreSQL | REST API backend, microservices |
| **mobile-app** | Kotlin + Jetpack Compose | Android native apps |
| **landing-page** | Next.js 14 (Static Export) | Marketing pages, waitlists |

Each template includes pre-configured `.opc/` files (PROJECT.md, REQUIREMENTS.md, ROADMAP.md, config.json).

## Core Workflows

### Product Development Pipeline
```
brainstorming → planning → implementing → reviewing → shipping
   (design)     (plan)     (TDD execute)   (review)    (ship)
```

### Business Decision Pipeline
```
find-community → validate-idea → mvp → first-customers → pricing → grow
  (community)    (validate)     (MVP)  (acquire)       (price)   (growth)
```

### Quality Assurance
```
TDD (test first) + debugging (root cause) + reviewing (5-dimension) + verifier (goal-reverse)
```

## Skills Overview

| Category | Count | Core Concept |
|----------|-------|-------------|
| Product Development | 5 | brainstorm → plan → implement → review → ship |
| Engineering Quality | 19 | TDD discipline + debugging + parallel execution + patterns |
| Business Operations | 18 | Lean startup + finance / legal / content / SEO / interviews |
| Market Intelligence | 2 | Multi-source research + builder tracking |
| Learning & Evolution | 3 | Learn from masters + create skills + continuous improvement |
| Meta-skills | 3 | How to correctly use SuperOPC in projects |
| **Total** | **51** | |

## Design Principles

1. **Skills First** — if a skill applies, use it, even with 1% probability
2. **TDD Discipline** — no production code without a failing test
3. **Business Mindset** — every technical decision considers ROI
4. **Minimalism** — minimize complexity, dependencies, operational cost
5. **Continuous Evolution** — the system learns from every interaction

## Roadmap

See the full evolution plan: **[ROADMAP.md](ROADMAP.md)**

| Phase | Version | Theme | Status |
|-------|---------|-------|--------|
| **Foundation** | v0.1–v0.5 | Skeleton → Skills → Agents → State → Engineering | Done |
| **Deepening** | v0.6–v0.9 | Business → Multi-runtime → Sessions → QA | Done |
| **Release** | v1.0.0 | Open-source release | Current |
| **Intelligence** | v1.1–v1.5 | Profiling → CLI → Security → Domain agents → Debug | Planned |
| **Platform** | v1.6–v2.0 | Workflow engine → i18n → Enterprise → SDK → OS | Planned |

## Contributing

We welcome contributions! You can:
- Report bugs
- Suggest new skills
- Improve existing skills
- Enhance documentation
- Add translations

See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines and [COMMIT_STYLE.md](COMMIT_STYLE.md) for commit conventions.

## Acknowledgments

SuperOPC stands on the shoulders of giants. Thanks to all open-source project authors:
- Jesse Vincent (Superpowers)
- TÂCHES (Get Shit Done)
- Sahil Lavingia (Minimalist Entrepreneur Skills)
- Nico Bailon (Everything Claude Code)
- And all contributors

## License

[MIT](LICENSE)
