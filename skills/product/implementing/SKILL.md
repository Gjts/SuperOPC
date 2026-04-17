---
name: implementing
description: Use when executing an approved PLAN.md with ready-for-build flag. Dispatches opc-executor agent which owns subagent dispatch, two-stage review, TDD enforcement, and atomic commits.
---

# implementing — 实现派发器

**触发条件：** 存在已通过 pre-flight gate 的 PLAN.md（含 `ready-for-build: true`），需要逐任务落成代码。适用于 "执行计划"、"开始实现"、"按 PLAN.md 做" 等场景。

**宣布：** "我调用 implementing 技能，派发给 opc-executor 持有完整实现 workflow。"

## 派发

使用 Task 工具派发 `opc-executor` agent：

- **输入：** PLAN.md 路径（必须含 `ready-for-build: true`）
- **输出：**
  - 每任务一个原子 commit
  - `docs/plans/<plan>.SUMMARY.md` 执行摘要
  - 最终全局代码审查判决

## 入口契约

- **接受**：`## OPC Pre-flight Gate` 中 `ready-for-build: true`
- **拒绝**：缺失 gate 或 `ready-for-build: false` → 回退到 `planning` skill

## 边界

- 本 skill **不执行** 任务提取、子代理派发、审查 —— 全部由 opc-executor 处理
- **不内联** TDD 细则（在 `tdd` skill）或派发协议（在 `agent-dispatch` skill）

## 关联

- **上游：** `planning` skill 产出 PLAN.md
- **下游：** 实现完成后走 `reviewing` skill（如需额外审查）或 `shipping` skill 发布
- **相关 agent：** opc-executor / opc-reviewer
- **相关 skill：** tdd（原子技术）/ agent-dispatch（原子技术）
