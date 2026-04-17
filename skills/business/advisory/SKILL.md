---
name: business-advisory
description: Use when the request involves one-person-company business decisions — pricing strategy, idea validation, MVP scope, first-customers acquisition, finding community, marketing plans, SEO, legal basics, finance ops, investor materials, user interviews, or any "how should I run my solo business" question. Dispatcher only — delegates to opc-business-advisor agent.
---

## 一人公司商业顾问派发器

**这是 dispatcher skill。不包含 workflow，统一派发给 `opc-business-advisor` agent。**

## 触发场景

自然语言关键词命中即激活：

- **定价 / 订阅 / freemium / 分层 / monetize / revenue**
- **验证想法 / 值得做吗 / 点子怎么样 / validate idea**
- **MVP / 最小可行产品 / 原型 / prototype**
- **找社区 / 在哪找用户 / niche / target audience**
- **前 100 个客户 / 冷启动 / early adopters / first customers**
- **SEO / 关键词 / 搜索排名**
- **内容 / 博客 / 社交文案 / 品牌声音 / copywriting**
- **营销 / growth / funnel / 转化 / A/B**
- **用户访谈 / The Mom Test / user interview**
- **融资 / 投资人 / pitch deck / investor**
- **法律 / 合同 / 条款 / ToS / privacy policy**
- **财务 / 税务 / 现金流 / finance ops**
- **价值观 / 文化 / 招聘 / company values**
- **产品思维 / product lens**
- **日常节奏 / daily standup / 自我管理**
- **商业决策审查 / minimalist review**

## 派发动作

1. **识别触发词**后立即调用：
   ```
   Task(subagent_type="opc-business-advisor", description="[子活动名称]", prompt="[用户原始请求 + 必要上下文]")
   ```
2. advisor 会在 Phase 0 完成子活动识别 + Anti-Build-Trap HARD-GATE 检查
3. advisor 会在 Phase 2 判断：委派给 domain agent（pricing / seo / content / growth）或按 `references/business/` 方法论本地执行
4. 等待 advisor 返回决策建议或转交通知

## 与其他 skill 的边界

- **非代码问题** → 本 dispatcher
- **涉及写代码 / 构建** → advisor 强制执行 Anti-Build-Trap；通过后建议派发 `product/planning`
- **需要调研证据** → advisor 会在执行中按需派发 `opc-researcher`

## 铁律

1. **dispatcher 不执行 workflow** —— 所有决策留给 opc-business-advisor
2. **触发后必须调用 Task()** —— 不要自行回复商业建议
3. **方法论源是 references/business/** —— advisor 不凭记忆编造框架

## 关联

- `agents/opc-business-advisor.md` —— workflow 持有者
- `references/business/*.md` —— 20 个子活动方法论手册
