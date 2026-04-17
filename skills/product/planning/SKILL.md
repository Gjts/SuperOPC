---
name: planning
description: Use when a design has been approved and needs to be broken into executable tasks with wave-based parallel optimization. Dispatches opc-planner agent which owns the full planning workflow (需求澄清 → 方案比较 → 任务分解 → 波次 → pre-flight gate).
---

# planning — 规划派发器

**触发条件：** 需要从需求或已批准的设计落成可执行的 PLAN.md。适用于 "规划 X"、"拆解 X"、"做个执行计划"、"把 X 分解成任务" 等场景。

**宣布：** "我调用 planning 技能，派发给 opc-planner 持有完整规划 workflow。"

## 派发

使用 Task 工具派发 `opc-planner` agent：

- **输入：** 需求描述 / 已批准的设计规格 / spec 文档路径
- **输出：** `docs/plans/YYYY-MM-DD-<feature>.md`，含：
  - `<opc-plan>` XML 主体（波次化任务）
  - `## OPC Plan Check`
  - `## OPC Assumptions Analysis`
  - `## OPC Pre-flight Gate`（含 `ready-for-build: true`）

## 边界

- 本 skill **不执行**任务分解、方案比较、gate 判决 —— 全部由 opc-planner 处理
- **不内联** PLAN.md 模板 —— 在 `references/plan-template.md`

## 关联

- **上游：** 需求模糊时走 `brainstorming` skill
- **下游：** PLAN.md 交付后走 `implementing` skill 执行
- **相关 agent：** opc-planner / opc-plan-checker / opc-assumptions-analyzer
