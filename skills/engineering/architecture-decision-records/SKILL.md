---
name: architecture-decision-records
description: Use when making significant architectural decisions — framework, library, pattern, database, API design. Captures context, alternatives, rationale as structured ADR documents that live alongside code.
---

## 架构决策记录（ADR）

**宣布：** "我正在使用 ADR 技能记录此架构决策。"

## 何时激活

- 在重大替代方案之间做选择（框架、库、模式、数据库）
- 用户说"记录这个决策"或"ADR this"
- 用户说"我们决定..."或"我们选 X 而不是 Y 是因为..."
- 用户问"为什么我们选了 X？"（查阅现有 ADR）
- 规划阶段讨论架构权衡

## ADR 格式

```markdown
# ADR-NNNN: [决策标题]

**日期**: YYYY-MM-DD
**状态**: proposed | accepted | deprecated | superseded by ADR-NNNN
**决策者**: [谁参与了决策]

## 背景

什么问题或情况促使了这个决策？

[2-5 句话描述情况、约束和驱动力]

## 决策

我们决定做什么？

[1-3 句话清晰陈述决策]

## 考虑的替代方案

### 替代方案 1: [名称]
- **优点**: [好处]
- **缺点**: [劣势]
- **淘汰原因**: [具体原因]

### 替代方案 2: [名称]
- **优点**: [好处]
- **缺点**: [劣势]
- **淘汰原因**: [具体原因]

## 后果

### 正面
- [好处 1]
- [好处 2]

### 负面
- [代价 1]
- [代价 2]

### 风险
- [风险 1] — 缓解：[措施]
```

## 文件组织

```
docs/adr/
  0001-use-nextjs-14-app-router.md
  0002-choose-supabase-over-firebase.md
  0003-adopt-stripe-for-payments.md
  README.md           # ADR 索引
```

## ADR 索引模板

```markdown
# Architecture Decision Records

| ADR | 标题 | 状态 | 日期 |
|-----|------|------|------|
| 0001 | 使用 Next.js 14 App Router | accepted | 2025-01-15 |
| 0002 | 选择 Supabase 而非 Firebase | accepted | 2025-01-16 |
| 0003 | 采用 Stripe 支付 | accepted | 2025-01-20 |
```

## 决策触发器

自动检测这些信号并建议创建 ADR：
- "我们应该用 X 还是 Y？"
- 安装新的主要依赖
- 创建新的架构层（如新增 service layer）
- 变更数据库设计或 API 协议
- 选择部署平台
- 采用新的设计模式

## ADR 生命周期

```
proposed → accepted → [may become] deprecated / superseded
```

- **proposed**：正在讨论，尚未确定
- **accepted**：已确定并开始实施
- **deprecated**：不再适用，但保留历史
- **superseded**：被新 ADR 取代（链接到新 ADR）

## 一人公司提示

- 一人公司 ADR **更重要**：6 个月后你不记得为什么这么决定
- 简洁 > 详尽：5 分钟写完，未来节省 5 小时调查
- 与 `.opc/PROJECT.md` 关键决策表联动
