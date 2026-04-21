---
name: implementing
description: Use when executing an approved PLAN.md with ready-for-build. Dispatches opc-executor, which owns implementation, TDD, review, and commits.
id: implementing
type: dispatcher
tags: [implementation, execute, build, tdd, commit, code]
dispatches_to: opc-executor
triggers:
  keywords: [实现, 执行, 开始实现, build, implement, 按计划, 开工]
  phrases: ["按 PLAN.md 做", "开始实现", "执行计划", "按计划执行", "开工"]
version: 1.4.1
---
# implementing — 实现派发器
**触发：** "执行计划"、"开始实现"、"按 PLAN.md 做"，且 PLAN.md 含 `ready-for-build: true`。
**宣布：** "我调用 implementing 技能，派发给 opc-executor 持有完整实现 workflow。"
## 派发
使用 Task 工具派发 `opc-executor` agent。
- **输入：** PLAN.md 路径；缺省时让 executor 查找最新可执行计划
- **输出：** 代码变更、原子 commit、执行摘要、最终审查判决
## 边界
- 本 skill 不提取任务、不派发子代理、不执行审查
- TDD 细则在 `tdd`；子代理协议在 `agent-dispatch`
- workflow 唯一事实源是 `agents/opc-executor.md`
