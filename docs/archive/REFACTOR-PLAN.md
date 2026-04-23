# SuperOPC 架构重构提案 v2

> Historical archive: this draft explains the refactor path that led to the current dispatcher architecture. It is kept for design history only. Current runtime contract lives in `AGENTS.md`, `README.md`, and the active command / skill / agent files.

> **状态：** 待审核（draft，不含代码改动）
> **日期：** 2026-04-17
> **目标：** 清理 command / agent / skill 三层的职责重叠
> **架构：** **skill 作为触发器 → agent 持有 workflow**
> **v2 关键改动：** 放弃 v1 "删除所有流程型 skill" 的方向，改为把它们**瘦身为派发器 skill**，充分利用 skill 的 auto-discovery

---

## 1. 为什么选 "skill 触发 agent" 而不是 "command 触发 agent"

| 维度 | command 入口（v1 方案） | **skill 入口（v2 方案）** |
|---|---|---|
| 触发方式 | 用户手动 `/opc-plan` | Claude 根据 `description` **自动匹配** |
| 发现成本 | 用户必须记命令名 | model 读过一次就会调 |
| 跨工具兼容 | 不同 IDE slash 命令不一致 | skill 是 Claude Code 原生机制，最稳 |
| 上下文开销 | 命令文件不进 system prompt | skill 文件按需加载 |
| v1 问题 | 删除 planning/implementing skill 后，model 无入口识别这些流程 | 保留 skill 作为路由层，流程入口自然被保留 |

> **结论：** skill 层是 Claude 认知系统里"该做什么"的**第一道识别网**，删掉等于把流程变成隐式。正确做法是**让 skill 变薄**，把实现推给 agent。

---

## 2. 三层新契约

```
┌────────────────────────────────────────────────────────────────┐
│ Command (可选、手动)                                            │
│   /opc-plan, /opc-build, /opc-ship — 用户想显式调用时用           │
│   内部只做一件事: 调对应 dispatcher skill                        │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ Skill (自动触发入口 + 原子技术)                                  │
│                                                                 │
│  ┌─ Dispatcher Skill (薄, ~20 行) ─────────────────────────┐   │
│  │   planning / implementing / reviewing / shipping        │   │
│  │   brainstorming / debugging-flow                        │   │
│  │   职责: 匹配场景 → Task(agent) 派发                      │   │
│  │   不含: workflow 步骤、评审维度、模板                     │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─ Atomic Skill (独立可复用技术) ─────────────────────────┐   │
│  │   tdd / verification-loop / debugging /                 │   │
│  │   git-worktrees / nextjs-patterns / business/*          │   │
│  │   职责: 单一技巧 + 红线 + 压力测试                       │   │
│  │   不含: agent 派发、跨阶段流程                           │   │
│  └─────────────────────────────────────────────────────────┘   │
└────────────────────────────────────────────────────────────────┘
                               │
                               ▼
┌────────────────────────────────────────────────────────────────┐
│ Agent (workflow 持有者)                                         │
│   opc-planner / opc-executor / opc-reviewer / opc-shipper       │
│   职责: 完整 workflow、门控判决、输出格式、协作链                 │
│   按需: Skill("tdd") / Skill("verification-loop") / 派发子 agent │
└────────────────────────────────────────────────────────────────┘
```

### 2.1 Dispatcher Skill 标准模板

每个 dispatcher skill ≤ 30 行，结构固定：

```markdown
---
name: planning
description: Use when design is approved and you need to break it into executable tasks. Dispatches opc-planner agent which owns the full planning workflow.
---

# planning — 规划派发器

**触发条件：** 设计规格已被用户批准，需要拆解为可执行计划。

**宣布：** "我调用 planning 技能，派发给 opc-planner 持有完整规划 workflow。"

## 派发

使用 Task 工具派发给 `opc-planner`：
- 输入: 设计规格 / 需求描述
- 输出: `docs/plans/YYYY-MM-DD-<feature>.md`（含 pre-flight gate 摘要）

## 不要做什么

- 不要在本 skill 内执行任务分解 — 那是 agent 的职责
- 不要内联 PLAN.md 模板 — 在 `references/plan-template.md`
- 不要做 plan-check / assumptions gate — agent 内部已处理

## 关联

- **下游**: `implementing` skill（执行 PLAN.md）
- **原子 skill**: tdd（规划阶段只是引用，不调用）
```

**关键：** dispatcher skill 不含流程细节，只负责：`何时触发 + 派发给谁 + 下游衔接`。

### 2.2 Atomic Skill 标准

保持当前 `tdd` / `verification-loop` 的写法：**红旗 + 步骤 + 压力测试**，不含 agent 派发。

### 2.3 三层"能与不能"

| 层 | 必须包含 | **不允许**包含 |
|---|---|---|
| Command | frontmatter + 1 句调用哪个 dispatcher skill | workflow 步骤、评审维度、模板 |
| Dispatcher Skill | 触发条件 + 派发目标 + 输入/输出契约 | 任务分解步骤、模板内容、评审维度 |
| Atomic Skill | 单一技巧 + 红线 + 压力测试 | agent 派发、跨阶段编排 |
| Agent | 完整 workflow + 门控 + 输出格式 | 原子技巧手把手步骤（TDD 的 RED 怎么写） |

---

## 3. 文件级 diff 预览

### 3.1 REWRITE 成 Dispatcher Skill（6 个，保留但瘦身）

原计划删除，v2 改为**瘦身为派发器**：

| 文件 | 现在行数 | 改后目标 | 内容去向 |
|---|---|---|---|
| `skills/product/brainstorming/SKILL.md` | 77 | ~25 | 流程搬到 `opc-planner.md` Phase 0；skill 只保留触发条件+派发 |
| `skills/product/planning/SKILL.md` | 84 | ~25 | PLAN.md 模板搬到 `references/plan-template.md`；流程在 `opc-planner.md` |
| `skills/product/implementing/SKILL.md` | 109 | ~25 | 流程搬到 `opc-executor.md`；skill 只派发 |
| `skills/product/reviewing/SKILL.md` | 81 | ~25 | 五维度审查搬到 `opc-reviewer.md` |
| `skills/product/shipping/SKILL.md` | 96 | ~25 | 4 选项流程搬到新建的 `opc-shipper.md` |
| `skills/using-superopc/workflow-modes/SKILL.md` | 66 | ~25 | 模式决策树搬到 `opc-orchestrator.md`；skill 只触发 |

### 3.2 MERGE（2 合 1，仍是 atomic skill）

| 合并源 | 合并目标 | 类型 |
|---|---|---|
| `skills/engineering/parallel-agents/` + `skills/engineering/subagent-driven-development/` | `skills/engineering/agent-dispatch/SKILL.md` | atomic（供 agent 内部调用）|

两者都是讲"如何派发子 agent"的原子技巧，应合一。

### 3.3 NEW（3 文件）

| 新建文件 | 职责 |
|---|---|
| `agents/opc-shipper.md` | 持有 ship workflow（测试验证 / 4 选项 / worktree 清理） |
| `references/plan-template.md` | PLAN.md XML + Markdown 混合模板（被 `opc-planner` 引用） |
| `references/review-rubric.md` | 五维度代码审查评分表（被 `opc-reviewer` 引用） |

### 3.4 EXTEND（agent 吸收完整 workflow，5 文件）

| Agent | 新增内容 |
|---|---|
| `agents/opc-planner.md` | Phase 0 需求澄清与方案比较（从 `brainstorming` skill 搬来）+ Phase 4 plan-check/assumptions gate（从 `/opc-plan` command 搬来） |
| `agents/opc-executor.md` | 完整子代理派发协议（从 `implementing` + `subagent-driven-development` 搬来） |
| `agents/opc-reviewer.md` | 补齐 reviewing skill 的差异维度（可维护性、成本考量） |
| `agents/opc-orchestrator.md` | 模式选择决策树（从 `workflow-modes` skill 搬来） |
| `agents/opc-shipper.md`（新） | 测试验证 + 4 选项 + worktree 清理 + 一人公司发布清单 |

### 3.5 REWRITE command 层（收敛入口，10+ 文件）

command 变成极薄壳，仅含"调哪个 dispatcher skill"：

| Command | 改后 |
|---|---|
| `commands/opc/plan.md` | 8 行：调用 `planning` skill |
| `commands/opc/build.md` | 8 行：调用 `implementing` skill |
| `commands/opc/review.md` | 8 行：调用 `reviewing` skill |
| `commands/opc/ship.md` | 8 行：调用 `shipping` skill |
| `/opc-do` `/opc-next` `/opc-discuss` `/opc-explore` `/opc-fast` `/opc-quick` | **合并为单个 `/opc`**，调用 `workflow-modes` dispatcher skill（由 orchestrator agent 决定模式） |

### 3.6 UNCHANGED（真正的 atomic skill，保留不动）

```
skills/engineering/tdd/
skills/engineering/debugging/
skills/engineering/verification-loop/
skills/engineering/git-worktrees/
skills/engineering/api-design/
skills/engineering/backend-patterns/
skills/engineering/frontend-patterns/
skills/engineering/dotnet-patterns/
skills/engineering/nextjs-patterns/
skills/engineering/kotlin-compose/
skills/engineering/postgres-patterns/
skills/engineering/docker-patterns/
skills/engineering/database-migrations/
skills/engineering/deployment-patterns/
skills/engineering/security-review/
skills/engineering/code-review-pipeline/
skills/engineering/codebase-onboarding/
skills/engineering/architecture-decision-records/
skills/engineering/e2e-testing/
skills/business/**  (19 个 solo-founder playbook)
skills/intelligence/**
skills/learning/**
skills/using-superopc/SKILL.md (元技能入口)
skills/using-superopc/developer-profile/
skills/using-superopc/session-management/
```

### 3.7 数据统计（v2）

| 项 | 改前 | 改后 | 变化 |
|---|---|---|---|
| Skill 文件数 | 58 | 57 | **-1**（仅合并 2→1）|
| 其中 dispatcher skill | 0 | 6 | +6（明确新角色）|
| 其中 atomic skill | 约 52 | 51 | -1 |
| Command 文件数 | 27 | 22 | **-5** |
| Agent 文件数 | 17 | 18 | **+1** |
| 总文件改动 | - | - | 约 **20** 文件 |

**vs v1 方案：** 删除行为从"大刀阔斧 -7 skill"变成"温和瘦身 -1 skill + 6 重写"，兼容性大大提升。

---

## 4. 触发链路示例

### 4.1 用户说"帮我规划登录功能"

```
user: "规划一下登录功能"
  ↓
Claude 匹配 description → 调用 planning skill
  ↓
planning skill (25 行): "派发给 opc-planner 持有完整规划 workflow"
  ↓
Task(opc-planner, "登录功能需求")
  ↓ (opc-planner agent 内部执行)
Phase 0: 需求澄清 (3-5 问)
Phase 1: 方案比较 (2-3 个方案)
Phase 2: 任务分解 (参考 references/plan-template.md)
Phase 3: 波次优化
Phase 4: plan-check + assumptions gate
  ↓
输出: docs/plans/2026-04-17-login.md (含 OPC Pre-flight Gate 摘要)
```

### 4.2 用户用 slash 命令

```
user: /opc-plan 登录功能
  ↓
commands/opc/plan.md (8 行): "调用 planning skill"
  ↓
planning skill → Task(opc-planner) → 同 4.1 流程
```

### 4.3 执行阶段调用原子技能

```
opc-executor agent 执行任务时:
  ↓
Skill("tdd") — atomic, 返回 RED-GREEN-REFACTOR 细则
  ↓
完成任务后
Skill("verification-loop") — atomic, 四层验证
```

---

## 5. 风险与兼容性

### 5.1 v2 相比 v1 的兼容性优势

- **所有 skill 名字保留**：外部文档/用户记忆中的 `planning` / `implementing` / `reviewing` skill 仍然存在，只是内容变薄
- **skill 自动触发链不断**：Claude 的 auto-discovery 仍能识别这些场景
- **scripts/convert.py 输出稳定**：Cursor/Windsurf 等下游工具看到的 skill 清单变化极小

### 5.2 需要同步的地方

- `.claude-plugin/plugin.json`：新增 `opc-shipper` agent 条目
- `CLAUDE.md` 架构说明段落：说明 "dispatcher vs atomic" 两类 skill
- `AGENTS.md` + `agents/registry.json`：新增 `opc-shipper`
- `CHANGELOG.md`：v1.3.0 重构说明

### 5.3 不在本次范围

- 不动 `agents/registry.json` 的 schema
- 不动 v2 engine（`scripts/engine/`）
- 不动 hooks / rules
- 不合并 `AGENTS.md` 与 `registry.json`（留给 v1.4.0）
- 不重构 `business/` 和 `intelligence/` skill

---

## 6. 执行阶段

### Phase A — 建立 dispatcher pattern（先开一条路验证）

**范围：** 选 1 条完整链路做样板，验证"skill → agent"的新模式好用再扩展。

**选 `planning` 链路：**

1. 瘦身 `skills/product/planning/SKILL.md` → ~25 行 dispatcher
2. 扩展 `agents/opc-planner.md` 吸收流程细节
3. 新增 `references/plan-template.md`
4. 薄化 `commands/opc/plan.md` → 8 行
5. 手动跑一次 `/opc-plan` 和 "规划一下 X" 两种入口，确认触发链正确

**提交：** `refactor(planning): adopt skill-dispatcher / agent-workflow pattern`

---

### Phase B — 复制 pattern 到其他 4 条链路

A 验证通过后，批量处理：

- `brainstorming` + 对应 agent 改动
- `implementing` + `opc-executor`
- `reviewing` + `opc-reviewer` + `references/review-rubric.md`
- `shipping` + 新建 `opc-shipper.md`

**提交：** `refactor(skills): apply dispatcher pattern to brainstorming/implementing/reviewing/shipping`

---

### Phase C — 合并 atomic skill + 收敛 command

1. 合并 `parallel-agents` + `subagent-driven-development` → `agent-dispatch`
2. 合并 6 个路由命令 → 单个 `/opc`
3. `workflow-modes` skill 瘦身为 dispatcher，派发 `opc-orchestrator`

**提交：** `refactor: consolidate atomic skills and collapse mode-router commands`

---

### Phase D — 全局一致性扫尾

- `AGENTS.md` / `CLAUDE.md` / `README.md` 更新架构说明
- `.claude-plugin/plugin.json` 同步
- CHANGELOG v1.3.0
- 跑一遍 `scripts/convert.py` 确认各 IDE 导出正确

**提交：** `docs: update architecture narrative for dispatcher/workflow split`

---

## 7. 成功标准

重构完成后应满足：

- [ ] 每个业务活动有**三个文件对应**：1 个 dispatcher skill（~25 行）+ 1 个 agent（持有流程）+ 1 个 command（~8 行）
- [ ] 所有 dispatcher skill 文件 ≤ 30 行，且**只含触发条件和派发目标**
- [ ] 所有 command 文件 ≤ 15 行
- [ ] atomic skill 里没有 `Task(` 或 `派发 agent` 这类语句
- [ ] agent 里没有 `调用 implementing 技能` 这类语句（agent 之间可协作，但不经过 dispatcher skill）
- [ ] `/opc-plan` 和自然语言 "规划 X" 能触发**完全相同**的 workflow

---

## 8. 下一步

回复：

- **"执行 A"** — 开始 planning 链路的样板改造，验证 pattern
- **"执行全部"** — 四阶段连续，每阶段独立 commit
- **"调整 X"** — 说明要改的条目
- **"先给我看 planning skill 瘦身后的样子"** — 我先把 `skills/product/planning/SKILL.md` 新版本贴出来，你确认后再动代码
