---
name: opc-plan
description: Plan a feature or phase using brainstorming → planning workflow
---

# /opc-plan — 规划功能

## 流程

1. **调用 brainstorming 技能**
   - 理解需求
   - 提出 2-3 个方案
   - 用户选择方案
   - 写设计规格

2. **调用 planning 技能**
   - 分解为原子任务
   - 分析依赖
   - 优化为波次
   - 输出 PLAN.md

3. **建议下一步**
   - 使用 `/opc-build` 执行计划
   - 或使用 `git-worktrees` 技能创建隔离环境

## 参数
- `$ARGUMENTS` — 要规划的功能描述
