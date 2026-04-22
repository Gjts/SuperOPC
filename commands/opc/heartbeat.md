---
name: opc-heartbeat
description: View cruise heartbeat — dispatches autonomous-ops skill which owns the workflow
---
# /opc-heartbeat — 巡航心跳入口
用户显式查看巡航状态。等价于自然语言 "看看心跳" / "cruise 状态"。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=heartbeat`。
autonomous-ops skill 会派发 `opc-cruise-operator` agent 执行 Heartbeat 子场景（读 `status.json` → 汇总运行状态、最近决策、异常信号）。该子场景是只读的。
## 参数
- `$ARGUMENTS` — 可选，`--json`
