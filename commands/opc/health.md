---
name: opc-health
description: Run project or repository integrity checks and optionally apply safe repairs
---
# /opc-health
质量健康检查入口。
## 动作
调用 `python scripts/opc_health.py $ARGUMENTS`。
默认诊断只读；`--repair` 会做受控本地修复。
## 参数
- `$ARGUMENTS` — 可选，`--cwd`、`--repair`、`--json`、`--target project|repo|all`
