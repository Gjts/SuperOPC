---
name: opc-autonomous
description: Bounded autonomous advance - dispatches autonomous-ops skill which owns the workflow
---
# /opc-autonomous
显式进入 bounded autonomous workflow。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并附加 `sub_scenario=autonomous-advance`。
`opc-cruise-operator` 要求 `--from/--to` 或 `--only` 边界；遇到 blocker、validation debt 或人工检查点时立即停止。
## 参数
- `$ARGUMENTS` - `--cwd`、`--from`、`--to`、`--only`、`--interactive`、`--json`
