---
name: opc-plan
description: Plan a feature or phase — dispatches planning skill which owns the workflow
---

# /opc-plan — 规划入口

用户显式触发规划流程。等价于自然语言 "规划 X"。

## 动作

调用 `planning` skill，传入 `$ARGUMENTS`。

planning skill 会派发 `opc-planner` agent 执行完整流程（Phase 0 需求澄清 → Phase 5 输出带 pre-flight gate 的 PLAN.md）。

## 参数

- `$ARGUMENTS` — 要规划的功能描述或 spec 文档路径
