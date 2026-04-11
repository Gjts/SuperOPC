# 示例 3：用 SuperOPC 运营一人公司

> 演示 SuperOPC 商业技能在产品验证、定价和增长中的应用

## 场景

你是独立开发者，有一个产品想法：**FocusBlock** — 帮助远程工作者用番茄钟 + 屏蔽干扰网站来提高专注力的浏览器扩展。

你需要验证这个想法是否值得投入时间开发。

## 工作流演示

### 第一阶段：想法验证

#### 1. 找到你的社区

```
/opc-do 找到 FocusBlock 的目标用户社区
```

SuperOPC 使用 `find-community` 技能：

```
## 社区调研结果

### 线上社区
- r/productivity (580 万成员) — 生产力工具讨论
- r/remotework (28 万成员) — 远程工作者聚集地
- Indie Hackers — 独立开发者社区
- ProductivityHub Discord — 专注力工具爱好者

### 竞品社区
- Forest App 用户群 — 移动端专注工具
- Cold Turkey 用户论坛 — 网站屏蔽工具

### 推荐策略
1. 在 r/productivity 发布 "你怎么处理浏览器干扰？" 的讨论帖
2. 在 Indie Hackers 分享构建过程
3. 在 Twitter/X 的 #buildinpublic 话题持续更新
```

#### 2. 用户访谈

```
/opc-do 准备 FocusBlock 的用户访谈提纲
```

SuperOPC 使用 `user-interview` 技能（The Mom Test 方法）：

```
## 访谈提纲（The Mom Test）

### 核心问题（关注行为，不问观点）
1. "上次你在工作中被打断专注是什么时候？具体发生了什么？"
2. "你试过什么方法来减少干扰？效果怎么样？"
3. "你现在用什么工具管理专注时间？花了多少钱？"
4. "如果有一个工具能 [价值主张]，你会用什么替代它？"

### 红旗信号
- "这个主意真棒！" → 礼貌但无用
- "我可能会用" → 没有具体行为承诺
- "你应该加上 X 功能" → 功能请求 ≠ 需求验证

### 绿旗信号
- "我每月花 $X 在 [竞品] 上" → 付费意愿
- "我上周刚因为 [问题] 浪费了 3 小时" → 真实痛点
- "你现在有 beta 版吗？我想试试" → 主动行动
```

#### 3. 竞品分析

```
/opc-research 浏览器专注力工具竞品分析
```

SuperOPC 使用 `market-research` + `follow-builders` 技能生成深度分析。

### 第二阶段：定价策略

```
/opc-do 设计 FocusBlock 的定价策略
```

SuperOPC 使用 `pricing` 技能：

```
## 定价策略分析

### 价值阶梯
| 方案 | 价格 | 功能 | 目标用户 |
|------|------|------|---------|
| Free | $0 | 基础番茄钟 + 3 个屏蔽网站 | 试用者 |
| Pro | $5/月 | 无限屏蔽 + 统计 + 多设备同步 | 个人用户 |
| Team | $3/人/月 | 团队仪表盘 + 管理员控制 | 小团队 |

### 定价依据
- 竞品锚点：Forest $2/月, Cold Turkey $39 一次性, Freedom $7/月
- 价值定位：介于免费工具和专业方案之间
- 最小收费建议：$5/月（验证付费意愿的最低门槛）

### 里程碑目标
- 100 免费用户 → 验证产品
- 20 付费用户 → 验证定价
- $1000 MRR → 可持续运营
```

### 第三阶段：MVP 构建

```
/opc-do 构建 FocusBlock MVP
```

SuperOPC 使用 `mvp` 技能确定最小功能集：

```
## MVP 范围（2 周可完成）

### 必须有（Week 1-2）
- 番茄钟计时器（25/5 分钟循环）
- 专注期间屏蔽指定网站
- Chrome 扩展基础 UI

### 可以没有（v2）
- 统计报表
- 多设备同步
- 团队功能
- 自定义时间

### 绝对不做（超范围）
- 移动端 App
- Firefox/Safari 扩展
- AI 智能推荐
```

### 第四阶段：增长

```
/opc-do 设计 FocusBlock 的增长策略
```

SuperOPC 使用 `first-customers` + `content-engine` + `seo` 技能：

```
## 前 100 个用户获取策略

### 第 1 周：手动推广
1. 在 r/productivity 分享构建故事
2. 在 Product Hunt 预热（Ship 页面）
3. 给 10 个生产力博主发邮件

### 第 2-4 周：内容营销
1. 写 3 篇 SEO 文章："best focus tools 2026"
2. Twitter/X #buildinpublic 每日更新
3. 在 Indie Hackers 发布月度复盘

### 第 5-8 周：产品驱动增长
1. 免费版自然传播
2. "Powered by FocusBlock" 水印（免费版）
3. 推荐奖励：邀请 3 人升级获得 1 个月免费 Pro
```

## 商业技能总结

| 技能 | 产出 |
|------|------|
| `find-community` | 3 个目标社区 + 参与策略 |
| `validate-idea` | 想法验证框架 + Go/No-Go 决策 |
| `user-interview` | The Mom Test 访谈提纲 + 信号识别 |
| `market-research` | 竞品矩阵 + 市场规模估算 |
| `mvp` | 最小功能集定义 + 时间估算 |
| `pricing` | 价值阶梯 + 里程碑目标 |
| `first-customers` | 前 100 用户获取策略 |
| `content-engine` | 内容日历 + 分发渠道 |
| `seo` | 关键词策略 + 内容集群 |
| `brand-voice` | 品牌语调 + 写作指南 |
| `legal-basics` | 隐私政策 + 服务条款 |
| `finance-ops` | MRR 追踪 + 财务仪表盘 |

## 一人公司时间分配建议

```
周一-周四: 开发（60%）
  上午：编码（使用 /opc-build）
  下午：测试和审查

周五: 商业（30%）
  上午：用户反馈和数据分析
  下午：内容创作和社区互动

周末: 学习和规划（10%）
  复盘本周进展（/opc-session-report）
  规划下周目标（/opc-next）
```
