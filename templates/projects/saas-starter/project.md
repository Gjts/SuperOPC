# [项目名称] — SaaS

## 这是什么

基于订阅模式的 SaaS 产品，帮助 [目标用户] 解决 [核心问题]。
用户通过自助注册、试用免费方案、升级付费计划来使用产品。

## 核心价值

让 [目标用户] 用最少的时间完成 [核心任务]，从而节省 [时间/金钱/精力]。

## 需求

### 已验证

（尚无 — 先发布后验证）

### 活跃

- [ ] 用户可以注册/登录（邮箱+密码 + OAuth）
- [ ] 用户可以查看仪表盘和核心功能
- [ ] 免费方案有使用限制，付费方案解锁完整功能
- [ ] 用户可以通过 Stripe Checkout 升级/降级订阅
- [ ] 用户可以管理账户设置和个人信息
- [ ] Landing page 清晰传达价值主张

### 超范围

- 团队协作 — v1 聚焦个人用户
- 移动端 App — v1 仅 Web 响应式
- 自建支付系统 — 使用 Stripe 托管

## 背景

- 技术栈：Next.js 14 + Supabase + Stripe + Vercel
- 目标市场：[市场描述]
- 竞品参考：[竞品 1]、[竞品 2]

## 约束

- **时间线**: 4-6 周 MVP — 一人开发
- **预算**: Supabase Free + Vercel Hobby 起步
- **性能**: 首屏加载 < 2s (LCP)
- **安全**: Supabase RLS + HTTPS + CSRF 防护

## 关键决策

| 决策 | 理由 | 结果 |
|------|------|------|
| Next.js App Router | Server Components 减少 JS bundle | — 待定 |
| Supabase 而非 Firebase | PostgreSQL + RLS + 开源 | — 待定 |
| Stripe Checkout | 减少 PCI 合规负担 | — 待定 |

---
*最后更新：[日期]，项目初始化*
