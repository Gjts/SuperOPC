---
name: opc
description: Natural-language entry for SuperOPC; dispatches workflow-modes skill for mode routing
---
# /opc
统一自然语言入口。用于用户不确定该进入 plan/build/review/ship/debug/business/next 哪条路径时。
## 动作
调用 `workflow-modes` skill，传入 `$ARGUMENTS`。
`workflow-modes` 会派发 `opc-orchestrator`，由 agent 持有 7 模式决策树与下游派发。
## 参数
- `$ARGUMENTS` — 自然语言请求或模式提示
