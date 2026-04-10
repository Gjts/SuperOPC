---
name: opc-build
description: Execute a PLAN.md with TDD enforcement and subagent-driven development
---

# /opc-build — 执行开发

## 流程

1. **查找最新的 PLAN.md**
   - 检查 `docs/plans/` 目录
   - 如果有多个计划，让用户选择
   - 如果没有计划，建议先用 `/opc-plan`

2. **调用 implementing 技能**
   - 逐任务执行
   - 每任务 TDD
   - 双阶段审查
   - 原子提交

3. **执行完成后**
   - 调用 reviewing 技能
   - 生成 SUMMARY.md
   - 建议 `/opc-ship` 发布

## 参数
- `$ARGUMENTS` — 可选，指定要执行的 PLAN.md 路径
