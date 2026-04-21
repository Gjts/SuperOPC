---
name: opc-cruise
description: Start autonomous cruise mode with zone-based permissions
---
# /opc-cruise
巡航模式入口。
## 动作
调用 `python scripts/engine/cruise_controller.py $ARGUMENTS` 或 `autonomous-ops` 规则。
按 watch / assist / cruise 权限区运行，并在 RED 区动作前停下。
## 参数
- `$ARGUMENTS` — 可选，`--mode watch|assist|cruise`、`--hours N`
