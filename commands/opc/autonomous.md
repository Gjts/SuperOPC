---
name: opc-autonomous
description: Bounded autonomous advance — dispatches autonomous-ops skill which owns the workflow
---
# /opc-autonomous — 有边界自主推进入口
用户显式进入"有边界自主推进"模式。等价于自然语言 "自动推进路线图" / "从 P1 跑到 P3"。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=autonomous-advance`。
autonomous-ops skill 会派发 `opc-cruise-operator` agent 执行 Autonomous-advance 子场景（边界确认 → HARD-GATE + Anti-Build-Trap 校验 → 循环派发 planning/implementing/reviewing/debugging skill → 遇 blocker/验证债务/人工检查点立即停止）。
## 🚨 HARD-GATE（进入前强制校验）
1. **边界必需**：`--from/--to` 或 `--only` 至少提供一个；无边界会被拒绝
2. **Anti-Build-Trap**：窗口内若有商业功能阶段，必须先有 validate-idea 证据
3. **每轮强制停点**：blocker / 新增 validation debt / 用户标注的人工检查点 → 立即停
4. **失败阈值**：连续 3 次失败 → emergency stop + 通知
## 常见错误与修复
- **"边界未指定" 被拒** → 加 `--from N --to M` 或 `--only K`
- **"Anti-Build-Trap 阻断"** → 先 `/opc-business` 走 validate-idea；完成后 `.opc/validation/` 会留记录
- **推进中 blocker** → cruise 自动停并写 HANDOFF.json；用 `/opc-resume` 查看停止点与下一步建议
## 参数
- `$ARGUMENTS` — 可选，`--cwd`、`--from`、`--to`、`--only`、`--interactive`、`--json`
