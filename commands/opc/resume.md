---
name: opc-resume
description: Resume session — dispatches session-management skill which owns the workflow
---
# /opc-resume — 恢复会话入口
用户显式触发会话恢复。等价于自然语言 "继续上次" / "从哪里开始"。
## 动作
调用 `session-management` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=resume`。
session-management skill 会派发 `opc-session-manager` agent 执行 Resume 子场景（读 `HANDOFF.json` → 校验 recovery files → 对齐 `STATE.md` → 重建当前位置 + 推荐一个主下一步）。
## 参数
- `$ARGUMENTS` — 可选，`--cwd <path>` 或恢复目标
