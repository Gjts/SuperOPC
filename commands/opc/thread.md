---
name: opc-thread
description: Create, list, or resume lightweight persistent context threads under .opc/threads
---
# /opc-thread
上下文线程入口。
## 动作
调用 `python scripts/opc_thread.py $ARGUMENTS`。
管理跨会话但未进入正式 roadmap 的轻量上下文。
## 参数
- `$ARGUMENTS` — thread 子命令、名称、备注或 `--cwd <path>`
