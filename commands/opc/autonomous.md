---
name: opc-autonomous
description: Bounded autonomous advance — dispatches autonomous-ops skill which owns the workflow
---
# /opc-autonomous — 有边界自主推进入口
用户显式进入"有边界自主推进"模式。等价于自然语言 "自动推进路线图" / "从 P1 跑到 P3"。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=autonomous-advance`。
autonomous-ops skill 会派发 `opc-cruise-operator` agent 执行 Autonomous-advance 子场景（边界确认 → HARD-GATE + Anti-Build-Trap 校验 → 循环派发 planning/implementing/reviewing/debugging skill → 遇 blocker/验证债务/人工检查点立即停止）。
## 参数
- `$ARGUMENTS` — 可选，`--cwd`、`--from`、`--to`、`--only`、`--interactive`、`--json`
