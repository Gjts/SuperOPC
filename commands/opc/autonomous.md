---
name: opc-autonomous
description: Advance a bounded roadmap slice autonomously while stopping at blockers or checkpoints
---
# /opc-autonomous
有边界自主推进入口。
## 动作
调用 `python scripts/opc_autonomous.py $ARGUMENTS`。
读取状态、确定推进窗口，并在 blocker、验证债务或人工检查点处停止。
## 参数
- `$ARGUMENTS` — 可选，`--cwd`、`--from`、`--to`、`--only`、`--interactive`、`--json`
