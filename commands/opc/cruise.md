---
name: opc-cruise
description: Start autonomous cruise mode — dispatches autonomous-ops skill which owns the workflow
---
# /opc-cruise — 巡航模式入口
用户显式进入巡航模式。等价于自然语言 "进入巡航" / "启动 cruise"。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=cruise-start`。
autonomous-ops skill 会派发 `opc-cruise-operator` agent 执行 Cruise start 子场景（HARD-GATE 校验 → 启动 `scripts/engine/cruise_controller.py` → 写入审计日志）。
## 参数
- `$ARGUMENTS` — 可选，`--mode watch|assist|cruise`、`--hours N`
