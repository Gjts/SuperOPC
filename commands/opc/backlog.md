---
name: opc-backlog
description: Park an idea in .opc/backlog without promoting it to the active roadmap
---
# /opc-backlog
待规划池入口。
## 动作
<!-- MIXED: list=readonly, create=writes .opc/todos/ -->
调用 `python scripts/opc_backlog.py $ARGUMENTS`。
保存、列出或提升暂不进入主路线图的事项。
- **只读模式**：不带参数时列出现有待办
- **写入模式**：带新事项时会在 `.opc/todos/` 创建单个 markdown 条目；stderr 会输出建议性 notice
  提示"需要规划评审时可改用 `/opc-plan`"。设 `OPC_SUPPRESS_WRITE_ADVISORY=1` 静音
## 参数
- `$ARGUMENTS` — backlog 子命令、事项或 `--cwd <path>`
