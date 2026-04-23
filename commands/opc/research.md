---
name: opc-research
description: "Run market research runtime: feed, insights, methods, report, and extracted-skill capture"
---
# /opc-research
市场研究入口。
## 动作
调用 `python bin/opc-tools research $ARGUMENTS`。
`methods` / `insights` 可直接消费；`feed` / `run` 会写 `.opc/` 研究产物。
## 参数
- `$ARGUMENTS` — research 子命令与参数，如 `run --query <topic>`
