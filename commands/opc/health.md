---
name: opc-health
description: Run project or repository integrity checks and optionally apply safe repairs
---
# /opc-health
质量健康检查入口。
## 动作
调用 `python scripts/opc_health.py $ARGUMENTS`。
检查 `.opc/`、agents、commands、hooks、skills、templates、链接和质量债务。
## 参数
- `$ARGUMENTS` — 可选，`--cwd`、`--repair`、`--json`、`--target project|repo|all`
