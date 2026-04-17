# SuperOPC — Agent Orchestration (v1.4, Dispatcher Pattern)

## 架构契约（v1.3 起，v1.4 锐化）

SuperOPC 采用三层 **skill-dispatcher / agent-workflow** 契约，加第四层 references：

~~~
Command (<= 15 行入口) ──> Dispatcher Skill (<= 30 行派发器) ──> Agent (完整 workflow)
                                                                      │
                                                                      ├─> Atomic Skill (单一技术)
                                                                      └─> references/ (知识库手册)
~~~

- **Command**：用户手动 slash 入口，仅派发对应 dispatcher skill
- **Dispatcher Skill**：auto-trigger 识别场景，`Task()` 派发 agent（共 8 个：planning / implementing / reviewing / shipping / debugging / security-review / business-advisory / workflow-modes）
- **Agent**：完整 workflow 持有者（唯一 source of truth）
- **Atomic Skill**（4 个）：tdd / agent-dispatch / verification-loop / git-worktrees —— 被 agent 按需调用
- **references/**（v1.4 新增层）：技术栈 patterns / 商业 playbook / rubric / checklist —— 由 agent workflow 按子活动引用，不作为 skill 暴露

## Agent Registry

全部 agent 注册在 `agents/registry.json`，含 capability_tags、scenarios、input/output 契约、priority。

`scripts/engine/dag_engine.py` 通过 registry 做**语义路由**（而非关键词匹配）。

### Agent 类型与数量（18 个）

- **core** (16)：内置专家（v1.4 新增 **opc-business-advisor**）
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

### 自主运营流水线（v2 engine）

~~~
事件 → decision_engine (三层决策) → dag_engine (波次编排) → registry (语义路由)
     → agent 执行 → quality_gate → state_engine → event_bus (循环)
~~~

### 巡航模式

~~~
cruise_controller → heartbeat → state_engine.load → decision_engine.decide
                  → zone_check → execute/escalate → notify → persist
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
