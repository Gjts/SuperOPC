---
name: opc-cruise
description: Start autonomous cruise mode — dispatches autonomous-ops skill which owns the workflow
---
# /opc-cruise — 巡航模式入口
用户显式进入巡航模式。等价于自然语言 "进入巡航" / "启动 cruise"。
## 动作
调用 `autonomous-ops` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=cruise-start`。
autonomous-ops skill 会派发 `opc-cruise-operator` agent 执行 Cruise start 子场景（HARD-GATE 校验 → 启动 `scripts/engine/cruise_controller.py` → 写入审计日志）。
## 🚨 Anti-Build-Trap 与边界硬门
`opc-cruise-operator` 进入前**强制**校验：
1. **边界**：必须提供 `--hours N`（默认 1）或 `--mode watch`；**无边界的 cruise 会被拒绝**
2. **Anti-Build-Trap**：若当前 `.opc/` 缺少 `validate-idea` 记录（`.opc/validation/` 为空）且 `ROADMAP.md` 中存在未验证的商业阶段，cruise 会被拒绝并建议先走 `/opc-business`
3. **RED 区动作**：部署 / DB migration / 支付配置等永远需要人工确认，cruise 自动升级到 notification，不会自动执行
4. **失败阈值**：连续 3 次失败触发 emergency stop，切回 ASSIST 或 WATCH
## 停止巡航
```
/opc-cruise stop                        # 优雅停止当前巡航（推荐）
python scripts/engine/cruise_controller.py stop  # 等价 CLI 路径
```
停止后写 `.opc/cruise-log/<date>.jsonl` 的 `cruise.stopped` 事件；若有未完成任务会写入 HANDOFF.json 便于后续 `/opc-resume`。
## 参数
- `$ARGUMENTS` — 可选，`--mode watch|assist|cruise`、`--hours N`
  - **watch**：只观察、报警，不执行任何动作
  - **assist**：执行 GREEN 区动作（测试 / 健康检查 / 文档），YELLOW/RED 暂停等待
  - **cruise**：执行 GREEN + YELLOW 区动作（代码变更、阶段推进、PR），RED 区仍需人工确认
