# SuperOPC 发布作战手册

> Archived launch asset for SuperOPC v1.1.0. Counts, feature lists, and release framing in this file are historical and should be refreshed before reuse.

> 版本：v1.1.0 发布
> 目标：7天内获得前100个 GitHub Stars + 前10个真实用户反馈

---

## 🎯 核心指标（North Star）


| 指标             | 7天目标        | 30天目标 |
| -------------- | ----------- | ----- |
| GitHub Stars   | 100         | 500   |
| 真实用户反馈         | 10          | 50    |
| ProductHunt 票数 | Top 10 当日   | —     |
| Twitter 线程互动   | 100 retweet | 500   |
| 中文社区讨论         | 50 赞        | —     |


---

## 📅 发布时间表

### Day 0（今天）— 准备完成 ✅

- v1.1.0 提交并推送到 GitHub
- Twitter 线程内容准备完毕
- 中文社区内容准备完毕
- ProductHunt 文案准备完毕

### Day 1（周二）— 英文社区发布

**时间：早上 9:00 EST（美国东部时间）**


| 时间    | 动作                  | 平台           |
| ----- | ------------------- | ------------ |
| 09:00 | 发布 Twitter 线程（10条推） | Twitter/X    |
| 09:30 | 提交 ProductHunt      | Product Hunt |
| 10:00 | 发布 r/ClaudeAI       | Reddit       |
| 10:30 | 发布 r/cursor         | Reddit       |
| 11:00 | 发布 IndieHackers     | IndieHackers |
| 14:00 | 发布 Show HN          | Hacker News  |
| 全天    | 回复所有评论              | 全平台          |


### Day 2（周三）— 中文社区发布

**时间：北京时间 上午 10:00**


| 时间    | 动作        | 平台   |
| ----- | --------- | ---- |
| 10:00 | 即刻发布（核心帖） | 即刻   |
| 11:00 | 知乎专栏文章    | 知乎   |
| 14:00 | V2EX 技术帖  | V2EX |
| 15:00 | 掘金技术文章    | 掘金   |
| 20:00 | 小红书图文     | 小红书  |


### Day 3-7 — 持续运营

- 每天回复 GitHub Issues 和 Discussions
- 每天在 Twitter 上回复 #buildinpublic #claudecode 相关内容
- 收集用户反馈，整理进 v1.2.0 计划

---

## 💬 评论回复模板

### 当有人问"怎么安装"

```
Setup is simple:

git clone https://github.com/gjts/superopc.git
cd superopc
python scripts/convert.py --tool cursor  # or claude-code, windsurf, copilot

Works with any AI tool you're already using. Full docs in the README.
```

### 当有人问"和 [其他工具] 有什么区别"

```
Great question. Most AI tools focus on code generation.

SuperOPC focuses on the full solo-founder workflow:
1. Business skills (validate before you build)
2. Engineering quality (TDD, security, review)
3. State management (context persists across sessions)
4. It exports to your existing tool — it's an OS layer, not a replacement.

What tool are you currently using? Happy to show a specific comparison.
```

### 当有人提 Bug 或建议

```
Thanks for this! Opening a GitHub issue to track it.

Would you be willing to share more context? [specific question]

This is exactly the kind of feedback that makes SuperOPC better.
```

---

## 📊 每日追踪

```
## SuperOPC 增长日志

### [日期]
- GitHub Stars: X
- 新 Issue/PR: X
- 最有价值的反馈: "..."
- 今日最高互动内容: [链接]
- 明日计划: ...
```

---

## 🔄 反馈 → 迭代流程

```
用户反馈 → 分类（bug/feature/doc）
        → bug: 本周修复
        → feature: 投票排序 → v1.2.0 计划
        → doc: 立即改进
```

---

## 💰 变现路径（30天后评估）

1. **GitHub Sponsors**：目标 $100/月（验证付费意愿）
2. **Pro 功能**（v2.0 后）：
  - 私有技能市场
  - 团队版（多人共享状态）
  - 高级 agent 模板
3. **Claude Code Marketplace**：当官方市场开放时，优先上架

---

## 📁 文件索引


| 文件                           | 用途                       |
| ---------------------------- | ------------------------ |
| `twitter-launch-thread.md`   | Twitter 10条推文，直接复制粘贴     |
| `chinese-community-posts.md` | 即刻/知乎/V2EX/掘金/小红书内容      |
| `producthunt-launch.md`      | PH 发布文案 + Show HN + 评论模板 |
| `LAUNCH-PLAYBOOK.md`         | 本文件，总指挥手册                |

