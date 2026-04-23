# IndieHackers + Reddit 帖子内容

> Archived launch asset for SuperOPC v1.1.0. Counts, feature lists, and release framing in this file are historical and should be refreshed before reuse.

---

## 一、IndieHackers — 产品发布帖

### 标题

```
I merged 9 open-source AI projects into one operating system for solo founders
```

### 正文

```
Hey IH 👋

I've been building solo for a while and kept running into the same problem:

I had great AI tools (Claude, Cursor) but no system. My .cursorrules were
a mess. Every project started from scratch. And none of my AI tools could
tell me to stop building and go validate my idea first.

So I spent months merging the best AI engineering projects from open source
into one thing: SuperOPC.

---

**What it is:**

An operating system for one-person companies. Not a standalone app — it's
a layer that goes on top of whatever AI coding tool you already use.

**24 skills across 4 domains:**
- Business: validate-idea, find-community, pricing, MVP, first-customers, user-interview, SEO, content-engine, legal-basics, finance-ops
- Engineering: TDD, debugging, parallel agents, security-review
- Intelligence: market-research, follow-builders, autonomous-ops
- Product: brainstorming, planning, implementing, reviewing, shipping

**15+ specialist agents** with a DAG engine that routes tasks semantically.

**11 AI runtime exports** — Claude Code, Cursor, Windsurf, Copilot, Gemini CLI, and 6 more.

**v2 autonomous engine** — event bus → decision engine → cruise mode.

---

**What makes it different:**

Most AI tools focus on code generation. SuperOPC focuses on the *full
solo-founder workflow*:

1. Business skills are baked in (validate before you build)
2. Cross-session memory via .opc/ state directory
3. Developer profiling — AI learns your work style over time
4. It's a merger of community best practices, not invented from scratch

---

**The origin story:**

I fused 9 open source projects:
- Superpowers (skill system + TDD)
- Get Shit Done (command system + wave execution)
- Minimalist Entrepreneur Skills (10 business skills)
- Everything Claude Code (continuous learning)
- Agency-Agents (192 specialist agent definitions)
+ 4 more

Standing on the shoulders of giants.

---

**Metrics:**
- v1.1.0 released today
- 24 skills, 15+ agents, 20+ commands
- MIT license, free forever
- Built using SuperOPC itself (dogfooding)

---

**GitHub:** https://github.com/Gjts/SuperOPC

Would love your feedback, especially:
1. Which skill/agent would be most useful to you?
2. What's the biggest gap in your current AI workflow?
3. Pricing thoughts for a potential Pro tier?

Thanks for reading 🙏
```

---

## 二、Reddit — r/ClaudeAI

### 标题

```
I built an operating system for Claude Code — 24 skills, 15 agents, works in 5 minutes
```

### 正文

```
Hey r/ClaudeAI,

Long-time Claude user here. I kept running into the same friction:

- Skills/rules scattered everywhere
- Claude forgets context every session
- No system for business decisions (validate before building)
- No quality gates (TDD, security review)

So I built SuperOPC — a layer that gives Claude a structured OS:

**24 skills:**
- Business: validate-idea, pricing, first-customers, user-interview, SEO...
- Engineering: TDD, debugging, security-review, parallel-agents...
- Intelligence: market-research, follow-builders, autonomous-ops

**15+ specialist agents** with semantic routing:
`opc-planner → opc-executor → opc-reviewer → opc-verifier → opc-debugger`

**State management:**
`.opc/` directory persists your project state across sessions — Claude
remembers what you're building and how you like to work.

**New in v1.1.0:**
- Developer profiling (8-dimension model)
- Cross-session learning store
- Subagent-driven development with dual-phase review

**Setup:**
```bash
git clone https://github.com/gjts/superopc.git
# Use directly as Claude Code plugin source
```

Also exports to Cursor, Windsurf, Copilot, and 8 more tools.

MIT, free. Full repo: [https://github.com/Gjts/SuperOPC](https://github.com/Gjts/SuperOPC)

Happy to answer any questions about the architecture or skill design.

```

---

## 三、Reddit — r/cursor

### 标题
```

SuperOPC: Turn your Cursor .cursorrules into a structured 24-skill operating system

```

### 正文
```

Hey everyone,

If your .cursorrules file has grown into an unmanageable mess (mine had),
you might find this useful.

SuperOPC is an operating system layer for solo founders. It exports a
structured skill/agent system directly into Cursor:

**Setup:**

```bash
git clone https://github.com/gjts/superopc.git
cd superopc
python scripts/convert.py --tool cursor
cp -r integrations/cursor/.cursor /your-project/
```

**What you get in Cursor:**

- 24 structured skills (not just rules — methodologies)
- 15+ specialist agents with clear roles
- Business skills alongside engineering (validate ideas, pricing, etc.)
- Developer profiling that remembers your preferences
- Cross-session learning

**The key difference from raw .cursorrules:**
Rules are static. Skills are methodologies with pressure-tested workflows.
When you invoke `validate-idea`, it walks you through a real validation
process before touching code.

Also works with Claude Code, Windsurf, Copilot, and 8 more tools.

GitHub: [https://github.com/Gjts/SuperOPC](https://github.com/Gjts/SuperOPC)

Questions welcome!

```

---

## 四、Reddit — r/SideProject

### 标题
```

Show HN/IH: After 9 months building solo, I made an AI operating system for one-person companies

```

### 正文
```

Built this because I needed it.

**The problem:** I had Claude, Cursor, random Notion prompts, scattered
.cursorrules files. Powerful tools, no system. And nothing stopped me
from building features nobody wanted.

**What I built:** SuperOPC — an operating system layer that goes on top
of any AI coding tool.

**What's inside:**

- 24 skills (business + engineering + market intelligence)
- 15+ specialist agents
- State management across sessions
- Autonomous mode (runs safe tasks while you sleep)
- Works with 11 AI tools

**What I'm proud of:**

1. Business skills are first-class (validate-idea runs BEFORE any code)
2. It's a fusion of 9 community projects — not invented from scratch
3. I'm using it to build itself (true dogfooding)

**Current status:**

- v1.1.0 shipped today
- MIT, free forever
- Looking for early users and feedback

**GitHub:** [https://github.com/Gjts/SuperOPC](https://github.com/Gjts/SuperOPC)

What would make this most useful for your solo projects?

```

---

## 五、Hacker News — Show HN

### 标题
```

Show HN: SuperOPC – AI operating system for one-person companies

```

### 正文
```

I merged 9 open-source AI workflow projects into a unified operating system
for solo founders.

The problem I was solving: Claude Code and Cursor are excellent, but they
don't give you a system. You end up with powerful tools and no methodology.
Crucially, nothing prevents you from building before you validate.

SuperOPC is a content/plugin layer (not a service) that provides:

1. 24 skills spanning business and engineering:
  - Business: validate-idea, pricing, MVP, user-interview, SEO, legal
  - Engineering: TDD, debugging, security-review, parallel agents
  - Intelligence: market-research, autonomous-ops
2. 15+ specialist agents with a semantic DAG router:
  opc-planner → opc-executor → opc-reviewer → opc-verifier
3. Cross-session state via .opc/ directory (persists context between
  Claude/Cursor sessions)
4. Developer profiling: 8-dimension model that evolves from usage patterns
5. Export to 11 AI tools: Claude Code, Cursor, Windsurf, Copilot, Gemini
  CLI, OpenCode, Codex, Trae, Cline, Augment, OpenClaw

Source projects fused:

- Superpowers (obra) — skill system + TDD
- Get Shit Done — command system + wave execution
- Minimalist Entrepreneur Skills — 10 business skills
- Everything Claude Code — continuous learning + agent delegation
- Agency-Agents — 192 specialist agent definitions

- 4 more

Interesting technical decisions:

- Skills are methodologies (not just prompts) with pressure-test scenarios
- Business skills are first-class, not an afterthought
- The validate-idea guardrail is enforced before any code generation
- Anti-pattern library with 24 rules embedded in every workflow

The repo itself is built using SuperOPC (dogfooding throughout).

MIT license. Feedback welcome, especially on the skill design and agent
routing architecture.

[https://github.com/Gjts/SuperOPC](https://github.com/Gjts/SuperOPC)

```

```
