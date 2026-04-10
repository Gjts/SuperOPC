---
name: skill-from-masters
description: Use when you want to learn from industry experts and encode their knowledge into a reusable skill. Turn expert knowledge into actionable AI skills.
---

## 从大师学习

**宣布：** "我正在使用 skill-from-masters 技能来从专家那里学习并创建新技能。"

## 方法论

### 第一步：识别领域和专家

1. **确定你要学的领域**（如定价、写作、产品设计）
2. **找到 1-3 个该领域的顶尖专家**
3. **定位他们的核心作品**（书籍、演讲、文章）

#### 专家识别标准
- ✅ 有实践成果（不只是理论）
- ✅ 有成体系的方法论
- ✅ 被同行认可
- ❌ 只有大量粉丝但无实践

### 第二步：提取核心方法论

从专家的作品中提取：

```markdown
## [专家] 的 [领域] 方法论

### 核心理念
[一句话总结]

### 关键原则
1. [原则 1] — [解释]
2. [原则 2] — [解释]
3. [原则 3] — [解释]

### 实操步骤
1. [步骤]
2. [步骤]

### 常见错误
- [错误 1]
- [错误 2]

### 金句 / 锚点
- "[原话]" — 触发正确行为的提醒
```

### 第三步：转化为 SKILL.md

将提取的方法论转化为 SuperOPC 技能格式：

```yaml
---
name: [技能名]
description: [何时使用这个技能]
---
```

关键要求：
- **description 只写触发条件**，不总结工作流
- **包含反模式和红旗**：防止 AI 合理化绕过
- **有具体的输出格式**：让结果可预期
- **有检查清单**：确保步骤不被跳过

### 第四步：测试技能

用压力场景测试新技能：
1. 在没有技能的情况下运行场景
2. 记录 AI 的行为和合理化借口
3. 安装技能后重新运行
4. 确认技能纠正了之前的偏差

## 方法论数据库参考领域

| 领域 | 推荐专家 |
|------|---------|
| 写作 | William Zinsser, Barbara Minto |
| 产品 | Marty Cagan, Teresa Torres |
| 定价 | Patrick Campbell |
| 营销 | Seth Godin, April Dunford |
| 面试用户 | Rob Fitzpatrick (The Mom Test) |
| 战略 | Michael Porter, Hamilton Helmer |

## 输出
一个完整的 SKILL.md 文件，可直接添加到 SuperOPC 技能系统中。
