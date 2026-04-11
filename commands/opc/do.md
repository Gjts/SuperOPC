---
name: opc-do
description: Route a natural-language intent to the most appropriate existing SuperOPC command, skill, or workflow mode
---

# /opc-do — 自然语言意图路由

## 定位

把用户的一句自然语言需求路由到最合适的现有 SuperOPC 工作流。

目标不是发明新流程，而是优先复用已有 `/opc-*` 命令和 skills。

## 流程

1. **理解意图**
   - 用户是想讨论、规划、执行、审查、发布，还是查看状态

2. **匹配现有入口**
   - 讨论 / 澄清 → `/opc-discuss`
   - 探索问题空间 → `/opc-explore`
   - 规划功能 → `/opc-plan`
   - 快速微任务 → `/opc-fast`
   - 小任务流程 → `/opc-quick`
   - 执行计划 → `/opc-build`
   - 代码审查 → `/opc-review`
   - 发布 → `/opc-ship`
   - 质量健康检查 / 完整性诊断 → `/opc-health`
   - 查看状态 → `/opc-progress` / `/opc-dashboard` / `/opc-stats`

3. **输出路由结果**
   - 给出推荐命令
   - 简要说明为什么
   - 必要时补一句“你也可以直接用 X”

## 约束

- 优先路由到已有命令/技能
- 只有当现有入口都不合适时，才建议继续讨论

## 参数

- `$ARGUMENTS` — 自然语言任务描述
