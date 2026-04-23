---
name: opc-resume
description: Resume session - dispatches session-management skill which owns the workflow
---
# /opc-resume
显式进入 resume workflow。
## 动作
调用 `session-management` skill，传入 `$ARGUMENTS`，并附加 `sub_scenario=resume`。
`opc-session-manager` 会从 `HANDOFF.json` 或 `STATE.md` 重建当前位置；handoff 缺失时回退到 state-based recovery。
## 参数
- `$ARGUMENTS` - 可选，`--cwd <path>` 或恢复目标
