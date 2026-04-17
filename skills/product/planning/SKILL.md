---
name: planning
description: Use when a new feature / product / significant change is requested, OR when a design has been approved and needs to be broken into executable tasks. Covers both 需求澄清（原 brainstorming）+ 规划分解. Dispatches opc-planner agent which owns the full Phase 0-5 workflow.
---

<HARD-GATE>
需求未澄清 / 设计未批准前，禁止任何代码生成、脚手架、文件修改。由 opc-planner
Phase 0-1 HARD-GATE 强制执行。
</HARD-GATE>

# planning — 规划派发器（含需求澄清）

**触发条件：**

- 新功能 / 新产品 / 重大变更请求（"我想做 X"、"有个想法"、"怎么实现 X"）
- 已批准设计需要落成可执行 PLAN.md（"规划 X"、"拆解 X"、"做执行计划"）

**宣布：** "我调用 planning 技能，派发给 opc-planner 持有完整 Phase 0-5 workflow。"

## 派发

使用 Task 工具派发 `opc-planner` agent：

- **输入：** 需求描述（模糊 / 已澄清皆可）/ 已批准的设计规格 / spec 文档路径
- **opc-planner 会自动识别阶段：**
  - 需求模糊 → Phase 0 需求澄清（5 问清单）
  - 设计未选 → Phase 1 方案比较（2-3 方案对比 + 一人公司适配度）
  - 设计已批准 → Phase 2-5 任务分解 → 波次优化 → pre-flight gate
- **输出：** `docs/plans/YYYY-MM-DD-<feature>.md`，含：
  - `<opc-plan>` XML 主体（波次化任务）
  - `## OPC Plan Check`
  - `## OPC Assumptions Analysis`
  - `## OPC Pre-flight Gate`（含 `ready-for-build: true`）

## 边界

- 本 skill **不执行**任何 workflow 步骤 —— 全部由 opc-planner 处理
- **不内联** PLAN.md 模板 —— 在 `references/plan-template.md`
- **HARD-GATE 保留**：Phase 0-1 未通过前 opc-planner 会拒绝进入任务分解

## 关联

- **workflow 持有者：** `agents/opc-planner.md`（Phase 0-5 完整流程）
- **pre-flight gate：** opc-plan-checker + opc-assumptions-analyzer
- **下游：** PLAN.md 交付后走 `implementing` skill 执行

## 迁移说明（v1.4）

v1.3 及之前 `skills/product/brainstorming/` 独立 skill 已合并到本 skill。
brainstorming 原本也是派发给 opc-planner 的 Phase 0-1，与本 skill 入口重复。
v1.4 起统一由 `planning` skill 触发，opc-planner 自动路由到合适的 Phase。
