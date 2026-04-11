---
name: opc-discuss
description: Enter discussion-only mode to clarify goals, trade-offs, and scope without making changes
---

# /opc-discuss — 纯讨论模式

## 定位

只讨论，不执行，不写文件，不进入实现。

适合：
- 需求还不清楚
- 需要做取舍
- 想先比较方案
- 当前有 blocker，需要先澄清

## 流程

1. **澄清目标**
   - 用户真正要解决的问题是什么
   - 成功标准是什么
   - 当前约束和风险是什么

2. **比较选项**
   - 给出 2-3 个可行方向
   - 说明优点、风险、复杂度

3. **收敛下一步**
   - 继续讨论
   - 升级到 `/opc-explore`
   - 或进入 `/opc-plan` / `/opc-fast` / `/opc-quick`

## 约束

- 不进行代码修改
- 不生成实现产物
- 重点是澄清与收敛，而不是提前执行

## 参数

- `$ARGUMENTS` — 要讨论的问题、方向或决策点
