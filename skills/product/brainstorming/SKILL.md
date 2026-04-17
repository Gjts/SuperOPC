---
name: brainstorming
description: Use when a new feature, product, or significant change is requested and the requirement is not yet clear. HARD GATE — no code, no scaffolding, no implementation until design is approved. Dispatches opc-planner agent Phase 0-1 (需求澄清 + 方案比较).
---

<HARD-GATE>
Do NOT invoke any implementation skill, write any code, scaffold any project, or make any file changes until the user has explicitly approved the design.
</HARD-GATE>

# brainstorming — 需求澄清派发器

**触发条件：** 出现新功能、新产品、重大变更请求，但需求尚未清晰。适用于 "我想做 X"、"怎么实现 X"、"有没有办法 X" 等场景。

**宣布：** "我调用 brainstorming 技能，派发给 opc-planner 在 Phase 0-1 帮你先想清楚做什么和为什么做。"

## 派发

使用 Task 工具派发 `opc-planner` agent，显式要求只走 Phase 0-1：

- **输入：** 用户的模糊需求描述
- **输出：** 批准后的设计规格，保存到 `docs/specs/YYYY-MM-DD-<topic>.md`
- **后续：** 用户批准设计后，继续 Phase 2+（自动衔接 planning 流程）

## 边界

- 本 skill **不内联** 5 问清单或方案比较模板 —— 全部在 opc-planner Phase 0-1
- **HARD-GATE 保留**：设计未批准前禁止实现

## 关联

- **下游：** 设计批准后 opc-planner 自动继续 Phase 2 任务分解
- **平行：** 需求已明确时直接走 `planning` skill
