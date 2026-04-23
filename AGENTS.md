# SuperOPC — Agent Orchestration (v1.4.2, Dispatcher Pattern)

## 架构契约（v1.3 起，v1.4 锐化，v1.4.2 封堵所有断层）

SuperOPC 采用三层 **skill-dispatcher / agent-workflow** 契约，加第四层 references：

~~~
Command (<= 15 行入口) ──> Dispatcher Skill (<= 60 行派发器) ──> Agent (完整 workflow)
                                                                      │
                                                                      ├─> Atomic Skill (单一技术)
                                                                      └─> references/ (知识库手册)
~~~

- **Command**：用户手动 slash 入口，**必须**派发对应 dispatcher skill；不允许直接 `python scripts/*.py`（本地 runtime 白名单除外，见下）
- **Dispatcher Skill**：auto-trigger 识别场景，`Task()` 派发 agent（共 10 个：planning / implementing / reviewing / shipping / debugging / security-review / business-advisory / workflow-modes / session-management / autonomous-ops）
- **Agent**：完整 workflow 持有者（唯一 source of truth）
- **Atomic Skill**（4 个）：tdd / agent-dispatch / verification-loop / git-worktrees —— 被 agent 按需调用
- **references/**（v1.4 新增层）：技术栈 patterns / 商业 playbook / rubric / checklist —— 由 agent workflow 按子活动引用，不作为 skill 暴露

### 本地 runtime 白名单例外（v1.4.2 分两档）

下列 slash 命令**允许**直接调用 Python 脚本或 `bin/opc-tools` 本地 runtime，**不**默认派发 skill。分两档：

#### 档一：LOCAL RUNTIME（6 个，以查询为主）

这组命令提供低摩擦本地入口。`/opc-dashboard` 与 `/opc-stats` 是严格只读；`/opc-health`、`/opc-profile`、`/opc-research` 带受控本地写入子动作；`/opc-intel refresh` 仍必须走 agent。

| 命令 | 脚本 | 用途 |
|------|------|------|
| `/opc-health` | `scripts/opc_health.py` | 健康检查与安全修复（诊断默认只读；`--repair` 做受控本地修复） |
| `/opc-dashboard` | `scripts/opc_dashboard.py` | 项目面板（纯只读汇总） |
| `/opc-stats` | `scripts/opc_stats.py` | 统计指标（纯只读计数） |
| `/opc-intel` | `scripts/opc_intel.py` | 代码库情报（query/status/validate/snapshot/diff 走本地 runtime；`refresh` 走 `opc-intel-updater`） |
| `/opc-profile` | `scripts/opc_profile.py` | 开发者画像（读写本地 profile，不写项目 `.opc/`） |
| `/opc-research` | `scripts/opc_research.py` | 研究 runtime（`methods` / `insights` 可直接消费；`feed` / `run` 会写 `.opc/` 研究产物） |

**档一进入条件：**
1. 默认用于低摩擦查询、索引或本地工具动作；任何受控写入都必须在命令文档显式声明
2. 不触发**未声明的** agent 派发；若存在受控例外（如 `/opc-intel refresh`）必须写明 dispatcher 路径
3. 写入范围必须局限于本地 profile、`.opc/` 工具产物或安全脚手架修复；不得偷偷升级成复杂 workflow
4. 输出可被人类直接消费或给 AI 做摘要
5. 任何一条被违反 → 立即降级为档二或改为 dispatcher

#### 档二：MIXED LOW-FRICTION（3 个，列出只读 / 创建轻量写入）

这类命令在 **"列出 + 查询现有"** 模式下是只读，在 **"创建新条目"** 模式下会写入 `.opc/threads/`、`.opc/seeds/`、`.opc/todos/`。

| 命令 | 脚本 | 只读模式 | 写入模式 |
|------|------|----------|----------|
| `/opc-thread` | `scripts/opc_thread.py` | 列出 / 查询现有线程 | 创建新线程 → `.opc/threads/` |
| `/opc-seed` | `scripts/opc_seed.py` | 列出 / 查询现有种子 | 创建新种子 → `.opc/seeds/` |
| `/opc-backlog` | `scripts/opc_backlog.py` | 列出 / 查询现有待办 | 创建新待办 → `.opc/todos/` |

**档二进入条件：**
1. 写入**仅限轻量条目**（单个 markdown 文件，无状态转换、无 agent 调用）
2. 写入模式**必须** stderr 输出建议性 notice，提示"CLI 快速路径 OK；需要规划评审时用 `/opc-plan`"
3. 命令文档**必须**在 `## 动作` 段标注 `<!-- MIXED: list=readonly, create=writes <dir> -->`
4. 命令不触发任何 agent 派发或 skill 规则执行
5. `OPC_SUPPRESS_WRITE_ADVISORY=1` 环境变量可静音 notice（例如 CI 批量导入场景）
6. 任何写入超出"单文件 markdown 条目"范围 → 立即改为 dispatcher

**档二设计理由：** thread/seed/backlog 是"**快速捕获**"场景（想法 / 延后任务 / 跨会话笔记），强制走 agent workflow 会增加摩擦却不增加质量。但写入行为必须在协议层可见，不能伪装为纯只读。

#### 白名单之外的命令必须派发 dispatcher skill

`/opc-plan` `/opc-build` `/opc-review` `/opc-ship` `/opc` `/opc-pause` `/opc-resume`
`/opc-progress` `/opc-session-report` `/opc-cruise` `/opc-heartbeat` `/opc-autonomous`
`/opc-start` `/opc-debug` `/opc-security` `/opc-business` 等 **16 个命令**必须派发 dispatcher skill。
`scripts/verify_command_contract.py` lint 在 CI 中强制此规则（档二命令会额外检查 stderr advisory 与 MIXED 注释标注）。

## Agent Registry

全部 agent 注册在 `agents/registry.json`，含 capability_tags、scenarios、input/output 契约、priority。

`scripts/engine/dag_engine.py` 通过 registry 做 **capability-tag 路由**：显式 agent 优先，其次匹配 capability_tags / scenarios，最后才走关键词回退。

### Agent 类型与数量（27 个）

- **core** (20)：内置专家（v1.4 新增 **opc-business-advisor** / **opc-shipper** / **opc-intel-updater**；v1.4.2 新增 **opc-session-manager** / **opc-cruise-operator**）
- **matrix** (2)：专业执行代理（frontend-wizard / backend-architect）
- **domain** (5)：按需激活的领域代理（devops / seo / content / growth / pricing），由 opc-business-advisor 或核心 agent 委派

## 代理编排规则

主动委托，不需用户提示：

| 场景 | 委托给 | 触发入口 |
|------|--------|---------|
| 新功能 / 模糊需求 / 已批准设计 | **opc-planner** (Phase 0-5) → **opc-plan-checker** | `planning` skill / `/opc-plan`（v1.4 已吸收旧 brainstorming） |
| 代码编写 / 修改后 | **opc-executor** + **opc-reviewer** | `implementing` / `reviewing` skill |
| 发布 / 合并 / PR | **opc-shipper** | `shipping` skill / `/opc-ship` |
| Bug 修复或调试 | **opc-debugger** | `debugging` skill |
| 安全审计 | **opc-security-auditor** | `security-review` skill |
| 商业决策（定价/验证/MVP/获客/营销/SEO/法务/财务） | **opc-business-advisor** | `business-advisory` skill（v1.4 新增统一入口） |
| 市场 / 竞品调研 | **opc-researcher** | 自然语言（按 `references/intelligence/` 方法论执行） |
| 阶段完成验证 | **opc-verifier** | `verification-loop` skill |
| 多步骤复杂任务 | **opc-orchestrator** | `workflow-modes` skill / `/opc` |
| 会话暂停 / 恢复 / 进度 / 会话报告 | **opc-session-manager** | `session-management` skill / `/opc-pause` / `/opc-resume` / `/opc-progress` / `/opc-session-report` |
| 巡航 / 心跳 / 有边界自主推进 | **opc-cruise-operator** | `autonomous-ops` skill / `/opc-cruise` / `/opc-heartbeat` / `/opc-autonomous` |
| 文档生成 | **opc-doc-writer** → **opc-doc-verifier** | 自然语言 |
| 代码库理解 | **opc-codebase-mapper** | 自然语言（按 `references/patterns/engineering/codebase-onboarding.md`） |
| UI 审查 | **opc-ui-auditor** | 自然语言 |
| 隐藏假设分析 | **opc-assumptions-analyzer** | 由 opc-planner Phase 4 派发 |
| 产品路线图 | **opc-roadmapper** | 自然语言 |
| 前端实现 | **opc-frontend-wizard**（自动路由）| registry 语义匹配 |
| 后端 / API / DB | **opc-backend-architect**（自动路由）| registry 语义匹配 |
| 代码库索引刷新 | **opc-intel-updater** | `/opc-intel refresh` |
| CI/CD / 部署 | **opc-devops-automator**（领域）| 由 opc-business-advisor 或 opc-executor 委派 |
| SEO 优化 | **opc-seo-specialist**（领域）| 由 opc-business-advisor 委派（seo 子活动） |
| 内容创作 | **opc-content-creator**（领域）| 由 opc-business-advisor 委派（content-engine 子活动） |
| 增长策略 | **opc-growth-hacker**（领域）| 由 opc-business-advisor 委派（growth 子活动） |
| 定价策略 | **opc-pricing-analyst**（领域）| 由 opc-business-advisor 委派（pricing 子活动） |

## 代理协作流水线

### 产品开发主流水线（v1.4 精简）

~~~
需求 → planning skill                         → implementing skill → reviewing skill → shipping skill
       (opc-planner Phase 0-5 统一流程)       (opc-executor)        (opc-reviewer)    (opc-shipper)
       ├ Phase 0 需求澄清（吸收旧 brainstorming）
       ├ Phase 1 方案比较
       ├ Phase 2 任务分解
       ├ Phase 3 波次优化
       ├ Phase 4 opc-plan-checker + opc-assumptions-analyzer
       └ Phase 5 pre-flight gate → ready-for-build: true
~~~

### 商业活动流水线（v1.4 新增）

~~~
商业请求 → business-advisory skill → opc-business-advisor
         → Phase 0 子活动识别（20 个）
         → Anti-Build-Trap HARD-GATE（validate-idea + find-community 检查）
         → Phase 2 本地执行 或 委派 domain agent
             （seo / content / growth / pricing）
         → 按 references/business/<sub-activity>.md 方法论输出决策建议
~~~

### 快速任务路径

~~~
用户请求 → workflow-modes skill → opc-orchestrator 决策 → fast/quick → opc-executor
~~~

### 调试流水线

~~~
Bug 报告 → debugging skill → opc-debugger (假设-证据-排除) → opc-executor 修复 → opc-verifier 回归
~~~

### 安全审计流水线

~~~
代码变更 → security-review skill → opc-security-auditor (OWASP) → opc-reviewer (安全维度)
~~~

### 文档流水线

~~~
代码完成 → opc-doc-writer → opc-doc-verifier
~~~

### 规划验证流水线（opc-planner 内部）

~~~
需求 → opc-planner Phase 0-3 草稿 → opc-plan-checker (8维) + opc-assumptions-analyzer
      → 最多 3 轮修订 → ready-for-build: true → opc-executor (波次)
~~~

### 自主运营流水线（v2 engine，v1.4.2 封堵）

~~~
用户入口:  /opc-autonomous → autonomous-ops skill → opc-cruise-operator (边界确认+HARD-GATE)
引擎回路:  事件 → decision_engine (三层) → dag_engine (波次) → registry → agent 执行
          → quality_gate → state_engine → event_bus (循环)
~~~

**v1.4.2 关键修复：** cruise_controller._dispatch_command 不再把 PLAN/BUILD/REVIEW 重定向到
`opc_workflow.py progress` 只读查询，而是通过 `claude --print --agent <owner>` 真派发到
opc-planner / opc-executor / opc-reviewer / opc-debugger / opc-shipper / opc-researcher /
opc-session-manager。只有 GREEN 区的 HEALTH_CHECK / COLLECT_INTEL / RUN_TESTS / FORMAT_CODE /
GENERATE_DOCS 保留走只读脚本。

### 巡航模式

~~~
/opc-cruise → autonomous-ops skill → opc-cruise-operator → cruise_controller
            → heartbeat → state_engine.load → decision_engine.decide
            → zone_check → execute(agent)/escalate(RED) → notify → persist
~~~

## 代理矩阵路由协议（v2 engine）

dag_engine 匹配任务到最佳代理：

1. 检查任务是否显式指定了代理 → 直接使用
2. 读取 `agents/registry.json` 的 `capability_tags`
3. 任务标题 + 动作 与标签做语义匹配，计算得分
4. 选择最高得分代理
5. 无匹配（得分 0）→ 关键词回退路由
6. 执行失败 3 次 → 降级到 `opc-executor`
7. 降级也失败 → 发出 `decision.required` 事件，等待人工介入

## 安全准则

**每次提交前：**

- 无硬编码密钥
- 用户输入已验证
- SQL 注入防护（参数化查询）
- 错误消息不泄露敏感数据

## 代码风格

- **不可变性**：创建新对象，不修改现有对象
- **小文件**：200-400 行典型，800 行上限
- **函数 < 50 行**，嵌套 < 5 层
- **TDD**：先写测试（RED）→ 最小实现（GREEN）→ 重构（REFACTOR）—— 参考 `Skill("tdd")`

## 提交规范

格式：`<type>: <description>`

类型：feat、fix、refactor、docs、test、chore、perf、ci

## v1.3 / v1.4 重构迁移映射

如果有外部文档引用旧 skill / 命令，按下表迁移：

### v1.3 迁移

| 旧路径 | 新路径 |
|---|---|
| `Skill("parallel-agents")` | `Skill("agent-dispatch")` Mode B |
| `Skill("subagent-driven-development")` | `Skill("agent-dispatch")` Mode A |
| `/opc-do` | `/opc` + 自然语言 |
| `/opc-next` / `/opc-discuss` / `/opc-explore` / `/opc-fast` / `/opc-quick` | `/opc <mode>` |
| `skills/product/*` 中流程型描述 | 对应 agent 文件（workflow 持有者）|

### v1.4 迁移

| 旧路径 | 新路径 |
|---|---|
| `Skill("brainstorming")` | `Skill("planning")`（opc-planner 自动识别 Phase 0-1） |
| `Skill("find-community")` / `validate-idea` / `mvp` / `processize` / `first-customers` / `pricing` / `marketing-plan` / `grow-sustainably` / `company-values` / `minimalist-review` / `legal-basics` / `finance-ops` / `investor-materials` / `product-lens` / `seo` / `content-engine` / `brand-voice` / `user-interview` / `daily-standup` | `Skill("business-advisory")` → opc-business-advisor Phase 0 子活动识别 → 按 `references/business/<sub-activity>.md` 方法论执行 |
| `Skill("market-research")` / `Skill("follow-builders")` | `references/intelligence/<topic>.md`（由 opc-researcher 引用） |
| `Skill("nextjs-patterns")` / `dotnet-patterns` / `postgres-patterns` / `kotlin-compose` / `docker-patterns` / `deployment-patterns` / `api-design` / `architecture-decision-records` / `codebase-onboarding` / `database-migrations` / `e2e-testing` / `frontend-patterns` / `backend-patterns` | `references/patterns/engineering/<topic>.md`（由 opc-executor 按技术栈上下文引用） |
| `Skill("code-review-pipeline")` | `references/review-rubric.md`（由 opc-reviewer 以 Quick/Standard/Deep 深度引用） |
| `Skill("skill-from-masters")` / `Skill("writing-skills")` | `references/skill-authoring.md` |
| `skills/intelligence/autonomous-ops/` | `skills/using-superopc/autonomous-ops/`（移到元层） |

### v1.4.2 迁移（命令契约封堵）

| 旧路径 / 旧用法 | 新路径 / 新用法 | 原因 |
|---|---|---|
| `Skill("session-management")` 作为 meta skill 直接读规则 | `Skill("session-management")` 现为 dispatcher，自动派发 `opc-session-manager` | meta skill 被 slash 触发但无 agent 绑定，v1.4.2 封堵 |
| `Skill("autonomous-ops")` 作为 meta skill 直接读 zone 规则 | `Skill("autonomous-ops")` 现为 dispatcher，自动派发 `opc-cruise-operator` | 同上 |
| `python scripts/opc_pause.py` | `/opc-pause`（派发 session-management） | slash 命令必须走 dispatcher skill |
| `python scripts/opc_resume.py` | `/opc-resume`（派发 session-management） | 同上 |
| `python scripts/opc_progress.py` | `/opc-progress`（派发 session-management） | 同上 |
| `python scripts/opc_session_report.py` | `/opc-session-report`（派发 session-management） | 同上 |
| `python scripts/opc_autonomous.py` | `/opc-autonomous`（派发 autonomous-ops） | 同上 |
| `python scripts/engine/cruise_controller.py` (直接) | `/opc-cruise` / `/opc-heartbeat`（派发 autonomous-ops） | 同上 |
| `/opc-thread <new-name>` 直接创建（隐式写入） | 仍可用但命令文档强制标注 `<!-- MIXED: ... -->`，stderr 会输出 write-advisory | 档二 MIXED 白名单契约显式化 |
| `/opc-seed <new-idea>` / `/opc-backlog <new-item>` | 同上 | 同上 |
| cruise_controller._dispatch_command 中 PLAN/BUILD/REVIEW 路由到 `opc_workflow.py progress` | 改为通过 `claude --print --agent <owner>` 真派发对应 agent | 修复 v1.4.1 发现的"假派发"bug |
| 无命令契约 lint | `scripts/verify_command_contract.py` 在 CI 强制 | ADR-0004 决策落地 |
