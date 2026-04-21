---
name: continuous-learning
description: Use when you want to improve the SuperOPC system itself based on patterns observed in your workflow. Meta-skill for system evolution.
id: continuous-learning
type: learning
tags: [learning, patterns, instinct, evolution, meta-improvement]
triggers:
  keywords: [学习, 总结, pattern, instinct, 经验, 教训, 改进系统]
  phrases: ["总结经验", "把教训学下来", "改进 SuperOPC"]
version: 1.4.1
---

## 持续学习

**宣布：** "我正在使用 continuous-learning 技能来改进 SuperOPC 系统。"

## 学习循环

### 观察
在每次交互中注意：
- **用户纠正**：用户修改了 AI 的输出 → 记录模式
- **反复步骤**：同一操作被重复做 → 候选自动化
- **错误模式**：相同类型的错误反复出现 → 需要新技能/规则
- **效率低下**：某些工作流过于繁琐 → 需要优化

### 分析
定期（建议每周或每两周）：
1. 回顾最近的交互记录
2. 识别重复的模式
3. 分类：
   - **新技能候选**：反复出现的流程 → 考虑创建技能
   - **技能改进**：现有技能的漏洞 → 更新技能
   - **新代理候选**：反复需要的专业能力 → 考虑创建代理
   - **工作流优化**：低效的步骤 → 简化或自动化

### 行动
将分析结果转化为改进：

```markdown
## 学习记录 — [日期]

### 观察到的模式
1. [模式描述] — 出现 [N] 次

### 改进行动
| 模式 | 类型 | 行动 | 优先级 |
|------|------|------|--------|
| [模式] | 新技能 | 创建 [技能名] | 高/中/低 |
| [模式] | 技能改进 | 更新 [技能名] | 高/中/低 |
| [模式] | 工作流优化 | [优化描述] | 高/中/低 |
```

## 自动化观察管道 (v1.1)

SuperOPC 通过 PostToolUse 钩子自动捕获工具使用模式，无需手动记录。

### 数据流

```
工具调用 → observe.py (PostToolUse钩子)
  → ~/.opc/learnings/observations.jsonl (原始记录)
  → learning_store.detect_patterns() (模式检测)
  → learning_store.evolve_instincts() (本能生成)
  → context_assembler.py (注入相关本能到会话)
```

### 观察记录格式

每次工具调用自动记录：
- **工具名** — Edit/Bash/Read/Write/Task 等
- **行动类型** — git-commit/edit-test/shell/subagent 等
- **上下文** — 文件路径或命令片段
- **项目** — 当前工作的项目名
- **时间戳**

### 本能演化

当某个模式重复出现 ≥5 次时，自动创建「本能」（instinct）：
- 本能 = 一条高置信度的学习记录
- 本能会被注入到后续会话的上下文中
- 本能积累到一定量后，建议升级为技能/命令/代理

### 维护命令

- **模式检测**: `learning_store.detect_patterns()` — 分析观察日志
- **本能演化**: `learning_store.evolve_instincts()` — 将模式升级为本能
- **观察清理**: `learning_store.prune_observations(max_age_days=30)` — 清理过期记录

## 知识沉淀位置

| 类型 | 存储位置 |
|------|---------|
| 原始观察 | `~/.opc/learnings/observations.jsonl` |
| 本能/洞察 | `~/.opc/learnings/{category}/{id}.json` |
| 项目特定知识 | 项目的 docs/ 目录 |
| 通用工作流改进 | SuperOPC skills/ 更新 |
| 个人偏好和习惯 | `~/.opc/USER-PROFILE.json` |
| 技术决策记录 | ADR (Architecture Decision Records) |

## 一人公司学习原则

- **系统化**：不依赖记忆，写下来
- **可复现**：知识变成技能，不是笔记
- **渐进式**：每次改进一小步
- **实用主义**：只记录真正有用的，不做文档强迫症

## 何时触发
- 完成一个大功能后
- 遇到了反复出现的问题
- 用户明确要求改进系统
- 每两周例行检查

## 压力测试

### 高压场景
- 每次做完项目就直接切到下一个，不沉淀经验。

### 常见偏差
- 依赖记忆，不形成可复用模式。

### 使用技能后的纠正
- 把有效做法和失败教训结构化沉淀进系统。

