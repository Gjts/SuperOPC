# SuperOPC — Agent Orchestration

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
