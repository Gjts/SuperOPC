---
name: opc-stats
description: Emit machine-readable phase, plan, requirement, and git metrics for the current .opc project
---

# /opc-stats — 项目指标

## 流程

1. **读取 `.opc/` 工作状态**
   - 路线图阶段表
   - 需求复选框
   - STATE 当前焦点和阻塞
   - Git 分支 / 脏文件 / 最近提交（如果可用）

2. **输出结构化指标**
   - phasesCompleted / phasesTotal
   - plansCompleted / plansTotal
   - requirementsCompleted / requirementsTotal
   - blockers / todos / riskyDecisions
   - git branch / dirtyFiles / lastCommit

3. **用于自动化**
   - 适合接 `/opc-dashboard`
   - 适合 CI、日报、会话报告、管理面板

## 推荐脚本

```bash
python scripts/opc_stats.py
python scripts/opc_stats.py --cwd /path/to/project
```

输出为 JSON，可直接被其他脚本消费。

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 指向目标项目
