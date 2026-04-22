---
name: opc-progress
description: Show progress — dispatches session-management skill which owns the workflow
---
# /opc-progress — 进度与当前位置入口
用户显式查看项目进度。等价于自然语言 "现在进度" / "到哪了"。
## 动作
调用 `session-management` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=progress`。
session-management skill 会派发 `opc-session-manager` agent 执行 Progress 子场景（读 `STATE.md` → 五段式摘要 → 唯一一个推荐下一步）。
## 参数
- `$ARGUMENTS` — 可选，`--cwd <path>` 或 `--json`
