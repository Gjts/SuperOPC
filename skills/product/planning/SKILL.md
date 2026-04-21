---
name: planning
description: Use for new features, products, significant changes, or approved designs that need executable tasks. Dispatches opc-planner, which owns Phase 0-5.
id: planning
type: dispatcher
tags: [planning, design, decomposition, architecture, roadmap, phase-0-5]
dispatches_to: opc-planner
triggers:
  keywords: [规划, 拆解, plan, 计划, 设计, 任务分解, 怎么实现, brainstorm, 脑暴]
  phrases: ["帮我规划", "怎么实现", "拆一下任务", "做个计划", "怎么做这个"]
version: 1.4.1
---
<HARD-GATE>
需求未澄清 / 设计未批准前，禁止代码生成、脚手架、文件修改。由 opc-planner Phase 0-1 强制执行。
</HARD-GATE>
# planning — 规划派发器
**触发：** 新功能 / 新产品 / 重大变更 / "规划 X" / "拆解 X" / "怎么实现 X"。
**宣布：** "我调用 planning 技能，派发给 opc-planner 持有完整 Phase 0-5 workflow。"
## 派发
使用 Task 工具派发 `opc-planner` agent。
- **输入：** 用户需求、已批准设计、spec 路径或当前问题上下文
- **输出：** `docs/plans/YYYY-MM-DD-<feature>.md`
## 边界
- 本 skill 不执行 workflow；workflow 唯一事实源是 `agents/opc-planner.md`
- PLAN 模板在 `references/plan-template.md`
- 输出后下游走 `implementing` skill
