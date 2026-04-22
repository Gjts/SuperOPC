---
name: opc-build
description: Execute an approved PLAN.md — dispatches implementing skill which owns the workflow
---
# /opc-build — 执行入口
用户显式触发实现流程。等价于自然语言 "执行计划"。
## 动作
调用 `implementing` skill，传入 `$ARGUMENTS`（可选的 PLAN.md 路径）。
implementing skill 会派发 `opc-executor` agent 执行完整流程（入口门控 → 波次执行 → 双阶段审查 → 原子提交 → SUMMARY.md）。
## 入口要求
目标 PLAN.md 必须包含 `## OPC Pre-flight Gate` 且 `ready-for-build: true`。
## 🚨 Anti-Build-Trap 预警
因为 opc-planner 在生成 PLAN.md 时已强制做过 Anti-Build-Trap 证据检查，`/opc-build` 本身不再重复检查。但若你**跳过了 `/opc-plan`** 手工写 PLAN.md，opc-executor 会在 Phase 1 校验 PLAN.md 的 Pre-flight Gate 中是否包含以下之一：
- `validate-idea-recorded: true`
- `paid-customers-signal: <N>`
- `continuation-of: <existing-phase-ref>`
- `refactoring-only: true`

任一满足即通过；否则 opc-executor 会**拒绝执行**并建议先走 `/opc-business` → validate-idea。
## 常见错误与修复
- **`ready-for-build: false`** → 说明 opc-plan-checker 验证未通过；读 PLAN.md 末尾的"修订意见"，改完后 `/opc-plan --revise` 让 opc-planner 重新走 Phase 4-5
- **测试在执行中失败** → opc-executor 会自动派发 `opc-debugger`；如果连续 3 次修复失败会升级到 user interaction
- **与 main 分支冲突** → opc-executor 会暂停并建议 `/opc-ship` 先合并或切 worktree
## 参数
- `$ARGUMENTS` — 可选，指定要执行的 PLAN.md 路径；缺省时查找最新
