# SaaS Starter 模板

> Next.js 14 + Supabase + Stripe — 一人公司 SaaS 快速启动模板

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| 前端 | Next.js 14 (App Router) | React Server Components + Server Actions |
| 样式 | Tailwind CSS 3 | Utility-first CSS |
| 认证 | Supabase Auth | Email/Password + OAuth (Google, GitHub) |
| 数据库 | Supabase (PostgreSQL 15) | RLS + Edge Functions |
| 支付 | Stripe | Checkout + Customer Portal + Webhooks |
| 部署 | Vercel | 零配置部署 + Edge Runtime |

## 适用场景

- SaaS MVP / Micro-SaaS
- 订阅制产品
- 自助服务型 B2B 工具
- 内容平台 + 付费墙

## 使用方式

```bash
# 1. 初始化项目
/opc-start

# 2. 选择此模板
# SuperOPC 会复制 .opc/ 预配置到你的项目

# 3. 安装依赖
npx create-next-app@latest my-saas --typescript --tailwind --app --src-dir
cd my-saas
npm install @supabase/supabase-js @supabase/ssr stripe @stripe/stripe-js
```

## 预配置内容

```
.opc/
  PROJECT.md          # SaaS 项目定义（订阅模型 + 核心价值）
  REQUIREMENTS.md     # 典型 SaaS 需求（认证/仪表盘/支付/设置）
  ROADMAP.md          # 5 阶段路线图
  STATE.md            # 初始状态
  config.json         # 适合 SaaS 的工作流配置
```

## 推荐入口与参考组合

| 阶段 | 入口 / 参考 |
|------|------|
| 验证 | `/opc-business`（validate-idea / user-interview / product-lens 子活动） |
| 开发 | `/opc-plan` / `/opc-build` + `nextjs-patterns.md` + `postgres-patterns.md` + `api-design.md` |
| 支付 | `/opc-business`（pricing / finance-ops 子活动） |
| 增长 | `/opc-business`（seo / content-engine / first-customers 子活动） |
| 运维 | `references/patterns/engineering/deployment-patterns.md` + `Skill("security-review")` |

## 适配的规则

- `rules/typescript/` — Next.js 14 编码规范
- `rules/common/security.md` — OWASP 安全基线
- `rules/common/testing.md` — 测试优先

## 关键架构决策

1. **Server Components 优先** — 减少客户端 JS bundle
2. **Supabase RLS** — 行级安全，不依赖中间件鉴权
3. **Stripe Webhooks** — 支付状态同步，不轮询
4. **Edge Runtime** — API 路由尽可能使用 Edge
