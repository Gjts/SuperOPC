---
name: opc-progress
description: Show project position, completion, blockers, verification debt, and the recommended next action
---
# /opc-progress
进度与当前位置入口。
## 动作
调用 `python scripts/opc_progress.py $ARGUMENTS`。
输出当前阶段、完成度、债务、最近活动和一个主下一步。
## 参数
- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 或 `--json`
