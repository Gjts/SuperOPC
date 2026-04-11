---
name: opc-fast
description: Execute a single micro-task inline with minimal ceremony while preserving clear acceptance and verification
---

# /opc-fast — 微任务快执行

## 定位

`/opc-fast` 只处理**一个明确、低范围、可快速完成的微任务**。

它和 `/opc-quick` 的区别：
- `/opc-fast`：1 个微任务，行内推进，不展开完整任务列表
- `/opc-quick`：1-3 个任务的小流程，仍然有轻量规划和执行顺序

## 流程

1. **确认任务足够小**
   - 单文件或少量文件
   - 不需要正式 PLAN.md
   - 不涉及大范围设计分歧

2. **直接执行最小闭环**
   - 明确目标
   - 修改必要文件
   - 运行最小验证

3. **给出结果与下一步**
   - 说明是否已完成
   - 如果任务超出微任务范围，升级到 `/opc-quick` 或 `/opc-plan`

## 路由规则

- 小改动 / 小修复 / 小文档调整 → `/opc-fast`
- 需要 1-3 个步骤协同 → `/opc-quick`
- 需要设计方案或范围澄清 → `/opc-discuss` / `/opc-plan`

## 参数

- `$ARGUMENTS` — 微任务描述
