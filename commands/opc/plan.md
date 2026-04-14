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

2. **调用 `opc-planner` + planning 技能**
   - 分解为原子任务
   - 分析依赖
   - 优化为波次
   - 先输出草稿 PLAN.md

3. **强制 pre-flight gate**
   - 调用 `opc-plan-checker` 审查草稿 PLAN.md
   - 调用 `opc-assumptions-analyzer` 提取隐藏假设
   - 如果 `opc-plan-checker` 判决不是 `APPROVED`，必须回到 `opc-planner` 修订
   - 如果存在未缓解的高风险假设，必须将其转成显式任务、spike、验证步骤或回滚方案
   - 最多进行 3 次修订循环，仍未通过则升级给用户决策

4. **仅在 gate 通过后输出最终 PLAN.md**
   - 保留 `<opc-plan>...</opc-plan>` 机器可读主体
   - 在文末追加 `## OPC Plan Check`
   - 在文末追加 `## OPC Assumptions Analysis`
   - 在文末追加如下门控摘要，供 `/opc-build` 和 `opc-tools verify plan-structure` 复核：

```markdown
## OPC Pre-flight Gate

- plan-check: APPROVED
- assumptions: PASS
- ready-for-build: true
```

5. **建议下一步**
   - 使用 `/opc-build` 执行计划
   - 或使用 `git-worktrees` 技能创建隔离环境

## 强制规则

1. **未通过 pre-flight gate 不得交付 PLAN.md**
2. **高风险假设不能停留在口头层面**，必须落为任务、验证或缓解措施
3. **`ready-for-build: true` 是执行入口信号**，缺失时不得进入 `/opc-build`

## 参数
- `$ARGUMENTS` — 要规划的功能描述
