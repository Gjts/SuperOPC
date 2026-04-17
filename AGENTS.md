# SuperOPC — Agent Orchestration (v2, Dispatcher Pattern)

## 架构契约（v1.3 起）

SuperOPC 采用三层 **skill-dispatcher / agent-workflow** 契约：

~~~
Command (<= 15 行入口) ──> Dispatcher Skill (<= 30 行派发器) ──> Agent (完整 workflow)
                                                                      │
                                                                      └─> Atomic Skill (单一技术)
~~~

- **Command**：用户手动 slash 入口，仅派发对应 dispatcher skill
- **Dispatcher Skill**：auto-trigger 识别场景，`Task()` 派发 agent
- **Agent**：完整 workflow 持有者（唯一 source of truth）
- **Atomic Skill**：tdd / agent-dispatch / verification-loop 等原子技术，被 agent 按需调用

## Agent Registry

全部 agent 注册在 `agents/registry.json`，含 capability_tags、scenarios、input/output 契约、priority。

`scripts/engine/dag_engine.py` 通过 registry 做**语义路由**（而非关键词匹配）。

### Agent 类型与数量（17 个）

- **core** (15)：内置专家
- **matrix** (2)：专业执行代理（frontend-wizard / backend-architect）
- **domain** (5+)：按需激活的领域代理（devops / seo / content / growth / pricing）

## 代理编排规则

主动委托，不需用户提示：

| 场景 | 委托给 | 触发入口 |
|------|--------|---------|
| 复杂功能需求 | **opc-planner** → **opc-plan-checker** | `planning` skill / `/opc-plan` |
| 需求模糊、需要设计 | **opc-planner**（Phase 0-1）| `brainstorming` skill |
| 代码编写 / 修改后 | **opc-executor** + **opc-reviewer** | `implementing` / `reviewing` skill |
| 发布 / 合并 / PR | **opc-shipper** | `shipping` skill / `/opc-ship` |
| Bug 修复或调试 | **opc-debugger** | `debugging` skill |
| 市场 / 竞品调研 | **opc-researcher** | 自然语言 |
| 阶段完成验证 | **opc-verifier** | `verification-loop` skill |
| 多步骤复杂任务 | **opc-orchestrator** | `workflow-modes` skill / `/opc` |
| 安全审计 | **opc-security-auditor** | `security-review` skill |
| 文档生成 | **opc-doc-writer** → **opc-doc-verifier** | 自然语言 |
| 代码库理解 | **opc-codebase-mapper** | `codebase-onboarding` skill |
| UI 审查 | **opc-ui-auditor** | 自然语言 |
| 隐藏假设分析 | **opc-assumptions-analyzer** | 由 opc-planner Phase 4 派发 |
| 产品路线图 | **opc-roadmapper** | 自然语言 |
| 前端实现 | **opc-frontend-wizard**（自动路由）| registry 语义匹配 |
| 后端 / API / DB | **opc-backend-architect**（自动路由）| registry 语义匹配 |
| 代码库索引刷新 | **opc-intel-updater** | `/opc-intel refresh` |
| CI/CD / 部署 | **opc-devops-automator**（领域）| 自然语言 |
| SEO 优化 | **opc-seo-specialist**（领域）| 自然语言 |
| 内容创作 | **opc-content-creator**（领域）| 自然语言 |
| 增长策略 | **opc-growth-hacker**（领域）| 自然语言 |
| 定价策略 | **opc-pricing-analyst**（领域）| 自然语言 |

## 代理协作流水线

### 产品开发主流水线

~~~
需求 → brainstorming skill   → planning skill   → implementing skill → reviewing skill → shipping skill
       (opc-planner P0-1)     (opc-planner P2-5)  (opc-executor)       (opc-reviewer)    (opc-shipper)
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

## v1.3 重构迁移映射

如果有外部文档引用旧 skill / 命令，按下表迁移：

| 旧路径 | 新路径 |
|---|---|
| `Skill("parallel-agents")` | `Skill("agent-dispatch")` Mode B |
| `Skill("subagent-driven-development")` | `Skill("agent-dispatch")` Mode A |
| `/opc-do` | `/opc` + 自然语言 |
| `/opc-next` / `/opc-discuss` / `/opc-explore` / `/opc-fast` / `/opc-quick` | `/opc <mode>` |
| `skills/product/*` 中流程型描述 | 对应 agent 文件（workflow 持有者）|
