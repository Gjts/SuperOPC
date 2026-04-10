---
name: opc-ship
description: Complete development branch — verify tests, merge/PR, cleanup
---

# /opc-ship — 发布

## 流程

1. **调用 shipping 技能**
   - 验证所有测试通过
   - 显示变更概要
   - 呈现 4 个选项（合并/PR/保持/丢弃）
   - 执行用户选择
   - 清理 worktree（如适用）

## 参数
- 无（自动检测当前分支状态）
