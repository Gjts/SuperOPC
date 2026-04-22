---
name: opc-plan
description: Plan a feature or phase — dispatches planning skill which owns the workflow
---
# /opc-plan — 规划入口
用户显式触发规划流程。等价于自然语言 "规划 X"。
## 动作
调用 `planning` skill，传入 `$ARGUMENTS`。
planning skill 会派发 `opc-planner` agent 执行完整流程（Phase 0 需求澄清 → Phase 5 输出带 pre-flight gate 的 PLAN.md）。
## 🚨 Anti-Build-Trap 预警
若 `$ARGUMENTS` 描述的是**新的产品功能或商业想法**（不是技术重构、bug 修复、已有阶段的延续），opc-planner 的 Phase 0 会**强制检查**以下证据：
1. `validate-idea` 子活动是否已在 `.opc/validation/` 留下记录（用户访谈 / 付费意愿 / 等价信号）？
2. `find-community` 子活动是否已识别出目标社区与初步触达路径？

**任一缺失 → 规划会被拒绝**，并被改派发到 `business-advisory` skill → `opc-business-advisor` 走 validate-idea / find-community 子活动。这不是 bug，是铁律（参见 `CLAUDE.md` §Anti-Build-Trap Guardrail）。

如需跳过（已有付费客户 / 上下游项目决策 / 重构类任务），在 `$ARGUMENTS` 中明确声明"已有 X 付费客户/这是 Y 项目的阶段 N 延续"，opc-planner 会把这个声明记录到 PLAN.md 的 Pre-flight Gate。
## 参数
- `$ARGUMENTS` — 要规划的功能描述或 spec 文档路径
