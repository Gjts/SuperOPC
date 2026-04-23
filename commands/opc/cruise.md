---
name: opc-cruise
description: Start autonomous cruise mode - dispatches autonomous-ops skill which owns the workflow
---
# /opc-cruise
显式进入 cruise workflow。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并附加 `sub_scenario=cruise-start`。
`opc-cruise-operator` 负责边界检查、Anti-Build-Trap 和 RED 区动作拦截；高风险动作只升级，不自动执行。
## 参数
- `$ARGUMENTS` - `--mode watch|assist|cruise`、`--hours N`
