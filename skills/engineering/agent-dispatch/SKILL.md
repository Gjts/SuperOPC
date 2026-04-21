---
name: agent-dispatch
description: Atomic skill for dispatching subagents — covers both serial-with-review (single session, quality-first) and wave-based parallel (multi-session, speed-first) patterns. Called by orchestrator agents (opc-executor / opc-orchestrator) when they need to delegate atomic tasks to fresh subagent contexts.
id: agent-dispatch
type: atomic
tags: [subagent, parallel, dispatch, wave, orchestration]
triggers:
  keywords: [subagent, 波次, 子代理, 并行派发, wave, dispatch, 串行派发]
version: 1.4.1
---

# agent-dispatch — 子代理派发原子技能

SuperOPC 派发子代理的唯一权威实现。合并自 v1 的 `parallel-agents` 和 `subagent-driven-development` 两个 skill。

**宣布：** "我调用 agent-dispatch 技能派发子代理执行原子任务。"

## 两种模式

| 模式 | 何时用 | 吞吐 | 质量保证 |
|---|---|---|---|
| **串行 + 双阶段审查** (Mode A) | 任务独立、需要质量保证、人类编排器在场 | 低 | 强（每任务规格+代码质量审查）|
| **波次并行** (Mode B) | 任务多、独立性强、速度优先 | 高 | 中（波次间验证，波次内信任）|

## 刚性规则（两模式共用）

1. **新鲜上下文** —— 每个子代理独立上下文，不继承编排器会话
2. **精确任务描述** —— 提供完整任务文本（不要让子代理读计划文件）
3. **输入文件清单** —— 告诉子代理读哪些文件，不要内联
4. **输出规格** —— 明确产物格式和路径
5. **编排器不实现** —— 编排器只做上下文准备和派发

---

## Mode A — 串行 + 双阶段审查

**适用：** 单会话内逐任务完成，每任务经过规格审查和代码质量审查。

### 执行循环

~~~
for each task:
  ┌─────────────────────────────────────────────────────┐
  │ 1. 派发实现者子代理 (./implementer-prompt.md)        │
  │    └─ DONE / DONE_WITH_CONCERNS / NEEDS_CONTEXT /   │
  │       BLOCKED                                        │
  │    ↓                                                  │
  │ 2. 派发规格审查子代理 (./spec-reviewer-prompt.md)     │
  │    - ✅ → 继续                                        │
  │    - ❌ → 实现者修复 → 重审（循环）                    │
  │    ↓                                                  │
  │ 3. 派发代码质量审查子代理                             │
  │    (./code-quality-reviewer-prompt.md)                 │
  │    - ✅ → 标记完成                                    │
  │    - ❌ → 实现者修复 → 重审（循环）                    │
  └─────────────────────────────────────────────────────┘
~~~

### 实现者状态处理

| 状态 | 动作 |
|---|---|
| `DONE` | 进入规格审查 |
| `DONE_WITH_CONCERNS` | 评估疑虑：正确性问题先修，观察性问题记录后审查 |
| `NEEDS_CONTEXT` | 补充上下文后重新派发 |
| `BLOCKED` | 按升级协议处理（见下） |

### BLOCKED 升级协议

~~~
1. 上下文不足       → 补充上下文，同模型重试
2. 推理能力不足     → 换更强模型重试
3. 任务过大         → 拆分为子任务
4. 计划本身有问题   → 上报编排器 / 用户
~~~

**绝不**静默忽略升级，也不**无改变**地让同模型重试。

### 模型选择（成本优化）

| 任务类型 | 推荐模型 | 信号 |
|---------|---------|------|
| 机械实现 | 快速/低成本 | 1-2文件、明确规格、无设计判断 |
| 集成任务 | 标准 | 多文件协调、模式匹配 |
| 架构/审查 | 最强可用 | 设计判断、全局理解 |

### 提示模板（本目录）

- `./implementer-prompt.md` — 实现者子代理模板
- `./spec-reviewer-prompt.md` — 规格合规审查模板
- `./code-quality-reviewer-prompt.md` — 代码质量审查模板

### 红线（Mode A）

绝不：

- 跳过任一审查阶段
- 规格审查未通过时启动代码质量审查
- 并行派发多个实现子代理（串行模式的定义）
- 让子代理自己读计划文件
- 在 main/master 上直接实现（除非用户明确同意）
- 带未修复问题继续

---

## Mode B — 波次并行

**适用：** 从 PLAN.md 中按 `<wave>` 分组派发，波次内多子代理并行、波次间严格验证。

### 波次执行流程

~~~
for each wave in waves:
  1. 验证前置波次产物 (Pre-flight Gate)
     - 波次 N 全部任务: completed 或 failed
     - 依赖产物文件存在
     - 产物通过基本验证 (非空/语法正确)
  2. 为每任务创建独立子代理上下文
  3. 并行派发所有子代理
  4. 等待全部完成
  5. 收集结果 + 质量检查 (Revision Gate)
  6. 失败任务按失败处理表处理
~~~

### 失败处理表

| 情况 | 动作 |
|------|------|
| 单任务失败（非阻塞下游） | 标记失败，继续同波次其他任务 |
| 单任务失败（阻塞下游） | 重试 2 次；仍失败则暂停依赖链 |
| 波次 > 50% 任务失败 | 暂停整个执行，报告用户 |
| 全部成功 | 推进到下一波次 |

### 一人公司适配

- **小波次** —— 通常 2-4 个并行任务，不追求大规模并行
- **上下文预算** —— 每个子代理独立上下文，避免编排器上下文爆炸
- **快速失败** —— 早发现问题早停止
- **可恢复** —— 从失败波次恢复，不从头开始

### 红线（Mode B）

绝不：

- 忽略依赖关系，让并行互相踩踏
- 跳过波前验证
- 继续下一波次而前置波次有失败任务未处理
- 让波次规模爆炸（> 10 个并行）

---

## 子代理上下文模板（两模式共用）

~~~
---
任务: [具体任务描述 — 完整文本，不要只给 ID]
输入: [需要读取的文件列表]
输出: [预期产物的路径和格式]
约束: [时间/质量/安全要求]
上游依赖: [本任务依赖的产物或信息]
---
~~~

## 模式选择决策

~~~
任务之间有强审查需求？ ─是─→ Mode A（串行 + 双阶段）
            │
            否
            ↓
任务彼此独立 + 数量 > 3？ ─是─→ Mode B（波次并行）
            │
            否
            ↓
单任务直接派发实现者（简化模式）
~~~

## 关联

- **上游 agent：** opc-executor / opc-orchestrator（调用本 skill）
- **相关 skill：** tdd（子代理实现时遵循）/ verification-loop（波次验证）
- **相关 reference：** `references/plan-template.md`（任务结构）

## 压力测试

### 高压场景
- 任务很多想一股脑并行；或想跳过审查加速完成。

### 常见偏差
- 把 Mode A 的审查阶段跳过；或让 Mode B 的波次失败率 > 50% 还继续。

### 正确姿态
- 先判断任务形态，再选模式。Mode A 和 Mode B 的红线都不能突破。
