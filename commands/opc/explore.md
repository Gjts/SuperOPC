---
name: opc-explore
description: Explore a problem space through structured questions and discovery before choosing an implementation direction
---

# /opc-explore — 苏格拉底式探索

## 定位

`/opc-explore` 适合在问题还没被正确表述时，用提问和探索来发现更好的方向。

与 `/opc-discuss` 的区别：
- `/opc-discuss`：围绕已知问题做讨论和方案比较
- `/opc-explore`：通过连续提问帮助用户发现问题、边界和隐藏假设

## 流程

1. **提出探索性问题**
   - 真问题是什么
   - 谁受影响
   - 当前假设是什么
   - 什么证据支持这些假设

2. **识别隐藏结构**
   - 约束
   - 风险
   - 范围边界
   - 被忽略的替代路径

3. **收敛输出**
   - 问题定义
   - 推荐继续讨论、规划或研究

## 结果去向

- 需要方案对比 → `/opc-discuss`
- 需要正式设计/实现 → `/opc-plan`
- 需要外部信息 → `/opc-research`

## 参数

- `$ARGUMENTS` — 想探索的主题、困惑或方向
