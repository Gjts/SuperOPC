---
name: opc-session-report
description: Generate session report — dispatches session-management skill which owns the workflow
---
# /opc-session-report — 会话报告入口
用户显式生成会话报告。等价于自然语言 "生成会话报告" / "本次做了什么"。
## 动作
调用 `session-management` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=session-report`。
session-management skill 会派发 `opc-session-manager` agent 执行 Session-report 子场景（汇总最近会话 → STATE 快照 → 质量债务 → 写入 `.opc/session-reports/*.md`）。
## 参数
- `$ARGUMENTS` — 可选，`--cwd <path>` 或 `--json`
