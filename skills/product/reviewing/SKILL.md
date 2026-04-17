---
name: reviewing
description: Use after code is written or modified. Dispatches opc-reviewer agent which owns the 5-dimension review workflow (spec compliance / code quality / security / one-person-company maintainability / test coverage).
---

# reviewing — 审查派发器

**触发条件：** 代码已经完成或修改，需要质量审查。适用于 "审查一下"、"看看有没有问题"、"code review"、"质量检查" 等场景。

**宣布：** "我调用 reviewing 技能，派发给 opc-reviewer 持有完整审查 workflow。"

## 派发

使用 Task 工具派发 `opc-reviewer` agent：

- **输入：** 变更范围（git diff / 文件列表 / 分支名）
- **输出：** 标准 `## OPC Code Review` 报告 + 判决（PASS / NEEDS FIX / REJECT）

## 边界

- 本 skill **不内联**五维度细则或评分表 —— 在 `references/review-rubric.md`
- **不执行**审查逻辑 —— 在 `opc-reviewer` agent

## 关联

- **上游：** `implementing` skill 完成后可自动触发
- **下游：** 判决 PASS → `shipping` skill；REJECT → 回 `implementing` 修复
- **相关 agent：** opc-reviewer
- **评分表：** `references/review-rubric.md`
