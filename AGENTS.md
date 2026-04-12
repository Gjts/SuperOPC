# SuperOPC — Agent Orchestration (v2)

## Agent Registry

All agents are registered in `agents/registry.json` with capability tags, scenarios,
input/output contracts, and priority weights.  The DAG engine (`scripts/engine/dag_engine.py`)
uses this registry for **semantic task-to-agent routing** instead of keyword matching.

Agent types:
- **core** (15): Built-in specialists always available
- **matrix** (2): Specialized execution agents (frontend-wizard, backend-architect)
- **domain** (5+): Extended specialists activated on demand (devops, seo, content, growth, pricing)

## 代理编排规则

主动使用代理，不需要用户提示：

| 场景 | 委托给 |
|------|--------|
| 复杂功能需求 | **opc-planner** → **opc-plan-checker** |
| 代码编写/修改后 | **opc-reviewer** |
| Bug 修复或调试 | **opc-debugger** |
| 新功能实现 | 先用 TDD 技能，再委托 **opc-executor** |
| 市场/竞品调研 | **opc-researcher** |
| 阶段完成验证 | **opc-verifier** |
| 多步骤复杂任务 | **opc-orchestrator** |
| 安全审计 | **opc-security-auditor** |
| 文档生成 | **opc-doc-writer** → **opc-doc-verifier** |
| 代码库理解 | **opc-codebase-mapper** |
| UI 审查 | **opc-ui-auditor** |
| 隐藏假设分析 | **opc-assumptions-analyzer** |
| 产品路线图 | **opc-roadmapper** |
| 前端实现 | **opc-frontend-wizard** (自动路由) |
| 后端/API/DB | **opc-backend-architect** (自动路由) |
| 代码库索引刷新 | **opc-intel-updater** (由 /opc-intel refresh 派发) |
| CI/CD/部署 | **opc-devops-automator** (领域代理) |
| SEO 优化 | **opc-seo-specialist** (领域代理) |
| 内容创作 | **opc-content-creator** (领域代理) |
| 增长策略 | **opc-growth-hacker** (领域代理) |
| 定价策略 | **opc-pricing-analyst** (领域代理) |

## 代理协作模式

### 产品开发流水线
```
用户需求 → opc-planner (规划) → opc-executor (执行) → opc-reviewer (审查) → opc-verifier (验证)
```

### 市场研究流水线
```
用户问题 → opc-researcher (调研) → opc-planner (行动方案) → opc-executor (执行)
```

### 快速任务路径
```
用户请求 → opc-executor (直接执行) → opc-reviewer (审查)
```

### 调试流水线
```
Bug 报告 → opc-debugger (假设-证据-排除) → opc-executor (修复) → opc-verifier (回归验证)
```

### 安全审计流水线
```
代码变更 → opc-security-auditor (OWASP 扫描) → opc-reviewer (安全维度审查)
```

### 文档流水线
```
代码完成 → opc-doc-writer (生成文档) → opc-doc-verifier (验证准确性)
```

### 规划验证流水线
```
需求 → opc-planner → opc-plan-checker (8维度) → opc-assumptions-analyzer → opc-executor (波次执行)
```

### 自主运营流水线 (v2)
```
事件触发 → decision_engine (三层决策) → dag_engine (波次编排) → agent_registry (语义路由) → 执行 → quality_gate → state_engine (状态更新) → event_bus (循环)
```

### 子代理驱动开发流水线 (v1.1)
```
计划 → 提取任务 → [每任务: 派发实现者(fresh) → 规格审查 → 代码质量审查 → 标记完成] → 最终全局审查 → 分支完成
```

### 巡航模式流水线 (v2)
```
cruise_controller → heartbeat → state_engine.load → decision_engine.decide → zone_check → execute/escalate → notify → persist
```

## 代理矩阵路由协议 (v2)

DAG 引擎通过以下流程匹配任务到最佳代理：

1. 检查任务是否显式指定了代理 → 直接使用
2. 读取 `agents/registry.json` 中所有代理的 `capability_tags`
3. 将任务标题+动作与标签做语义匹配，计算得分
4. 选择最高得分的代理
5. 若无匹配（得分为0），使用关键词回退路由
6. 若执行失败 3 次，尝试降级到 `opc-executor`
7. 若降级也失败，发出 `decision.required` 事件，等待人工介入

## 安全准则

**每次提交前：**
- 无硬编码密钥
- 所有用户输入已验证
- SQL 注入防护（参数化查询）
- 错误消息不泄露敏感数据

## 代码风格

- **不可变性**：创建新对象，不修改现有对象
- **小文件**：200-400 行典型，800 行上限
- **函数 < 50 行**，嵌套 < 5 层
- **TDD**：先写测试（RED）→ 最小实现（GREEN）→ 重构（REFACTOR）

## 提交规范

格式：`<type>: <description>`

类型：feat, fix, refactor, docs, test, chore, perf, ci
