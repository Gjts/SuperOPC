---
name: workflow-modes
description: Use when deciding whether to discuss, explore, route, fast-execute, or recommend the next step in SuperOPC.
---

# 工作流模式

当任务的关键问题不是“做什么”，而是“现在该用哪种工作方式”时，使用本技能。

## 模式选择

### autonomous
用于在已知边界内连续推进一段路线图工作，并在 blocker、验证欠债或人工检查点处停下。

### discuss
用于澄清与取舍，不执行。

### explore
用于苏格拉底式提问，先发现真正的问题。

### fast
用于一个明确的微任务，直接行内完成。

### quick
用于 1-3 个任务的小流程。

### do
用于把自然语言意图路由到现有命令或技能。

### next
用于基于当前状态推荐一个主动作。

## 决策顺序

1. 问题是否已经定义清楚？
   - 否 → `explore`
2. 问题清楚但要做方案取舍？
   - 是 → `discuss`
3. 是否想在明确边界内连续推进，而不是每步都重新确认？
   - 是 → `autonomous`
4. 是否只是一个明确微任务？
   - 是 → `fast`
5. 是否需要轻量任务流？
   - 是 → `quick`
6. 用户只是说一句自然语言，不知道怎么开始？
   - 是 → `do`
7. 用户只想知道下一步？
   - 是 → `next`

## 原则

- 优先复用已有命令
- `do` 是路由器，不是新工作流引擎
- `fast` 不要膨胀成 `quick`
- `discuss` / `explore` 不要偷偷进入实现
