# Building in Public with SuperOPC | 用 SuperOPC 公开构建

> 一人公司创始人如何利用 SuperOPC 实践 Building in Public 策略

## 什么是 Building in Public

Building in Public（公开构建）是独立创始人通过公开分享产品开发过程来获取早期用户、建立信任和获得反馈的策略。

SuperOPC 的工作流天然适合 Building in Public —— 每一步都有结构化输出，可以直接转化为社交内容。

## 内容来源映射

| SuperOPC 产出 | 社交内容类型 | 发布平台 |
|---------------|-------------|---------|
| `/opc-start` 项目初始化 | "Day 1" 公告帖 | Twitter/X, 微信公众号, 知乎 |
| `/opc-research run --query <话题>` 市场调研 | 市场洞察长帖 | Twitter Thread, 小红书 |
| `/opc-plan` 功能规划 | "我在构建什么" | Indie Hackers, 即刻 |
| `/opc-build` 开发进展 | 进度更新 + 代码截图 | Twitter/X, 掘金 |
| `/opc-dashboard` 仪表盘 | 数据透明帖 | Twitter/X, Indie Hackers |
| `/opc-session-report` 会话报告 | 每周复盘 | Blog, Newsletter |
| `/opc-ship` 发布 | 发布公告 | Product Hunt, 微信, V2EX |
| `/opc-stats` 指标 | MRR / 用户数更新 | Twitter/X, Indie Hackers |

## 每周内容日历模板

### 周一：目标设定
```
/opc-progress
```
分享本周计划和目标，引用 SuperOPC 当前 session 的推荐下一步。

### 周二-周四：开发进展
```
/opc-progress
```
分享开发进展截图、代码片段、遇到的挑战。

### 周五：学到了什么
```
/opc-session-report
```
复盘本周学到的东西，包括技术决策和商业洞察。

### 周末：数据透明
```bash
python scripts/opc_stats.py --cwd .
```
分享关键指标（注册数、MRR、使用量）。

## 适用技能

| 技能 | 用途 |
|------|------|
| `content-engine` | 系统化内容生产和分发 |
| `brand-voice` | 保持一致的品牌语调 |
| `seo` | 博客文章的 SEO 优化 |
| `first-customers` | 从公开构建中获取早期用户 |
| `user-interview` | 将公开讨论转化为用户研究 |

## 实战建议

### 1. 内容格式模板

**进度更新帖（Twitter/X）：**
```
Day [N] of building [产品名]

What I did:
- [完成的任务 1]
- [完成的任务 2]

What I learned:
- [洞察]

Next:
- [下一步计划]

#buildinpublic #indiehacker
```

**数据透明帖：**
```
[产品名] - Month [N] update

Users: [X] → [Y] (+Z%)
MRR: $[X] → $[Y]
Biggest win: [描述]
Biggest challenge: [描述]

Full breakdown in thread
```

### 2. 渠道策略

| 渠道 | 内容类型 | 频率 |
|------|---------|------|
| Twitter/X | 进度更新、数据、洞察 | 每日 |
| Indie Hackers | 月度复盘、里程碑 | 每月 |
| Blog/Newsletter | 深度教程、经验总结 | 每两周 |
| Product Hunt | 版本发布 | 按里程碑 |
| 微信公众号 | 中文深度内容 | 每周 |
| 即刻/小红书 | 轻量进度更新 | 每日 |

### 3. 里程碑发布清单

用 SuperOPC 的 shipping 流程自然映射到公开发布：

```
1. /opc-ship 完成技术发布
2. 撰写发布公告（使用 brand-voice 技能保持语调）
3. Product Hunt 提交
4. 社交媒体多平台同步
5. 给 waitlist 用户发邮件
6. 在社区（Reddit/Indie Hackers）分享
```

## 常见问题

**Q：分享多少才合适？**
A：分享过程和学习，不分享敏感商业数据和安全细节。SuperOPC 的 `SECURITY.md` 中的建议同样适用于公开内容。

**Q：没人关注怎么办？**
A：保持一致性比完美更重要。前 30 天专注建立节奏，受众会自然增长。

**Q：如何平衡构建和分享的时间？**
A：使用 SuperOPC 的结构化输出（仪表盘、报告、进度）直接作为内容素材，减少额外的内容创作时间。目标是 80% 构建、20% 分享。
