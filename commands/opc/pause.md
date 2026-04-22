---
name: opc-pause
description: Pause session — dispatches session-management skill which owns the workflow
---
# /opc-pause — 暂停与交接入口
用户显式触发会话暂停。等价于自然语言 "暂停一下" / "先停这里"。
## 动作
调用 `session-management` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=pause`。
session-management skill 会派发 `opc-session-manager` agent 执行 Pause 子场景（写入 `.opc/HANDOFF.json`，更新 `STATE.md` 连续性字段，输出恢复提示）。
## 参数
- `$ARGUMENTS` — 可选，暂停原因、stop point、`--cwd <path>`
