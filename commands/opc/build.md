---
name: opc-build
description: Execute an approved PLAN.md - dispatches implementing skill which owns the workflow
---
# /opc-build
显式进入 implementing workflow。
## 动作
调用 `implementing` skill，传入 `$ARGUMENTS`。
`opc-executor` 仅执行 pre-flight gate 含 `ready-for-build: true` 的 PLAN.md；缺少继续执行信号时会拒绝构建。
## 参数
- `$ARGUMENTS` - 可选，目标 PLAN.md 路径
