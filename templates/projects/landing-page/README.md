# Landing Page 模板

> 静态营销页 — 快速验证想法、收集邮箱、引导转化

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| 框架 | Next.js 14 (Static Export) | 零 JS 默认 + 按需交互 |
| 样式 | Tailwind CSS 3 | 快速迭代 + 响应式 |
| 动画 | Framer Motion | 滚动动画 + 过渡效果 |
| 表单 | React Hook Form | 邮箱收集 + 验证 |
| 分析 | Plausible / Umami | 隐私友好分析 |
| 部署 | Vercel / Cloudflare Pages | 全球 CDN |

## 适用场景

- 产品发布前的预注册页
- 独立产品的营销主页
- A/B 测试不同价值主张
- 收集早期用户邮箱（waitlist）

## 使用方式

```bash
# 1. 初始化项目
/opc-start

# 2. 选择此模板

# 3. 创建项目
npx create-next-app@latest my-landing --typescript --tailwind --app
cd my-landing
npm install framer-motion react-hook-form
```

## 预配置内容

```
.opc/
  PROJECT.md          # Landing page 项目定义
  REQUIREMENTS.md     # 营销页需求（Hero/Features/CTA/SEO）
  ROADMAP.md          # 3 阶段路线图
  STATE.md            # 初始状态
  config.json         # 轻量工作流配置
```

## 推荐入口与参考组合

| 阶段 | 入口 / 参考 |
|------|------|
| 文案 | `/opc-business`（brand-voice / content-engine 子活动） |
| 开发 | `/opc-plan` / `/opc-build` + `nextjs-patterns.md` + `frontend-patterns.md` |
| SEO | `/opc-business`（seo 子活动） |
| 增长 | `/opc-business`（first-customers / validate-idea 子活动） |

## 页面结构

```
Landing Page
├── Hero Section          # 标题 + 副标题 + CTA
├── Social Proof          # Logo 墙 / 用户评价
├── Features              # 3-6 个核心功能卡片
├── How It Works          # 3 步流程图
├── Pricing               # 价格方案对比（可选）
├── Testimonials          # 用户证言
├── FAQ                   # 常见问题手风琴
├── Final CTA             # 底部行动号召
└── Footer                # 链接 + 社交媒体 + 法律声明
```

## 关键架构决策

1. **静态导出** — 零服务器成本，全球 CDN 分发
2. **Server Components** — 首屏零 JS，Lighthouse 100
3. **渐进增强** — 核心内容不依赖 JS，交互按需加载
4. **隐私优先分析** — Plausible/Umami 替代 Google Analytics
