---
name: opc-heartbeat
description: View cruise-mode status, recent decisions, and autonomous-operation health
---
# /opc-heartbeat
巡航心跳入口。
## 动作
调用 `python scripts/engine/cruise_controller.py heartbeat $ARGUMENTS`。
显示运行状态、最近决策和健康信号。
## 参数
- `$ARGUMENTS` — 可选，`--json`
