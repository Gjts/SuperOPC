---
name: business-advisory
description: "Use for one-person-company decisions: pricing, validation, MVP, customers, community, marketing, SEO, legal, finance, interviews, or growth. Dispatcher only; delegates to opc-business-advisor."
id: business-advisory
type: dispatcher
tags: [business, advisory, pricing, mvp, validate-idea, marketing, growth, legal, finance, seo]
dispatches_to: opc-business-advisor
triggers:
  keywords: [定价, 验证, mvp, 获客, 营销, seo, 法律, 财务, 访谈, pricing, marketing, validate, launch, 一人公司]
  phrases: ["怎么定价", "这个想法", "怎么获客", "一人公司", "要不要做这个"]
version: 1.4.1
---
# business-advisory — 商业顾问派发器
**触发：** 定价、验证想法、MVP、找用户/社区、获客、SEO、内容、营销、增长、访谈、法律、财务等商业问题。
**宣布：** "我调用 business-advisory 技能，派发给 opc-business-advisor 做子活动识别与决策。"
## 派发
使用 Task 工具派发 `opc-business-advisor` agent。
- **输入：** 用户原始商业问题 + 相关项目上下文
- **输出：** 子活动识别、Anti-Build-Trap 检查、reference-backed 建议或 domain agent 委派结果
## 边界
- 本 skill 不输出商业建议；所有决策留给 `opc-business-advisor`
- 方法论源是 `references/business/`
- pricing / seo / content / growth 由 advisor 按需委派 domain agent
