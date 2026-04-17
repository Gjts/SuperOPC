---
name: opc-ship
description: Complete development branch — dispatches shipping skill which owns the workflow
---

# /opc-ship — 发布入口

用户显式触发发布流程。等价于自然语言 "发布"。

## 动作

调用 `shipping` skill。

shipping skill 会派发 `opc-shipper` agent 执行完整流程（测试验证 → 一人公司发布清单 → 4 选项 → 执行 → worktree 清理）。

## 入口要求

- 已通过 `opc-reviewer` 审查判决 PASS
- 工作树干净（或由 shipper 给出警告）

## 参数

- 无（自动检测当前分支状态）
