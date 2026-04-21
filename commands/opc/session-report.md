---
name: opc-session-report
description: Summarize recent session activity, progress, blockers, next steps, and validation debt
---
# /opc-session-report
会话报告入口。
## 动作
调用 `python scripts/opc_session_report.py $ARGUMENTS`。
输出最近会话、当前状态、质量债务、handoff 和推荐下一步。
## 参数
- `$ARGUMENTS` — 可选，`--cwd <path>` 或 `--json`
