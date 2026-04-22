---
name: opc-thread
description: Create, list, or resume lightweight persistent context threads under .opc/threads
---
# /opc-thread
上下文线程入口。
## 动作
<!-- MIXED: list=readonly, create=writes .opc/threads/ -->
调用 `python scripts/opc_thread.py $ARGUMENTS`。
管理跨会话但未进入正式 roadmap 的轻量上下文。
- **只读模式**：不带参数或指向已有线程时，仅列出或打开现有线程
- **写入模式**：带新名称时会在 `.opc/threads/` 创建单个 markdown 条目；stderr 会输出建议性 notice
  提示"需要规划评审时可改用 `/opc-plan`"。设 `OPC_SUPPRESS_WRITE_ADVISORY=1` 静音
## 参数
- `$ARGUMENTS` — thread 子命令、名称、备注或 `--cwd <path>`
