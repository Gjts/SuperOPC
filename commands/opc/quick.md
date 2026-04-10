---
name: opc-quick
description: Execute a small ad-hoc task with quality guarantees but minimal ceremony
---

# /opc-quick — 快速任务

## 流程

快速模式使用同样的系统但路径更短：
- 跳过 brainstorming（直接到 planning）
- 跳过设计规格（直接到任务列表）
- 保留 TDD 和原子提交

1. **理解任务**
   - 用户描述要做什么

2. **快速规划**
   - 直接分解为 1-3 个任务
   - 不写正式的 PLAN.md

3. **执行**
   - TDD 执行每个任务
   - 原子提交

4. **完成**
   - 简要审查
   - 提交

## 参数
- `$ARGUMENTS` — 任务描述
