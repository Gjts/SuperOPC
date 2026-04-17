# Skill 撰写指南

> SuperOPC 的 skill 是对 AI 行为的定向纠偏工具。本参考文档合并了
> 原 `skills/learning/skill-from-masters/` 与 `skills/learning/writing-skills/`
> 两份指引，统一成一份 skill 作者手册，供开发者在创建新 skill 或改进
> 既有 skill 时查阅。
>
> **触发使用：** 当需要新建 / 修改 `skills/**/SKILL.md` 时。

## 总则

1. **只为真实失败写 skill** —— 没看见 AI 在没有 skill 时犯错，就不要写 skill
2. **先有方法论，再写 skill** —— 从大师 / 实战提炼原则，而非拍脑袋
3. **description 只写触发条件，不要总结工作流** —— 总结了 AI 会跳过内容
4. **skill 的测试方式是压力场景**，不是单元测试

---

## 一、从大师学习方法论（原 skill-from-masters）

### 第一步：识别领域和专家

1. 确定你要学的领域（如定价、写作、产品设计）
2. 找到 1-3 个该领域的顶尖专家
3. 定位他们的核心作品（书籍、演讲、文章）

**专家识别标准**

- ✅ 有实践成果（不只是理论）
- ✅ 有成体系的方法论
- ✅ 被同行认可
- ❌ 只有大量粉丝但无实践

### 第二步：提取核心方法论

从专家的作品中提取结构化输出：

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

### 第三步：转化为 SKILL.md 或 agent workflow

- 若提炼出的是**可复用的纪律 / 原子技术**（如 TDD、debugging 循环）→ 写成 skill
- 若提炼出的是**业务 workflow**（如规划、审查、发布）→ 写成 agent workflow，skill 只作 dispatcher

### 第四步：压力测试新 skill

1. 在没有 skill 的情况下运行真实场景
2. 记录 AI 的行为与合理化借口（逐字）
3. 安装 skill 后重新运行
4. 确认 skill 纠正了之前的偏差

### 方法论数据库参考领域

| 领域 | 推荐专家 |
|------|---------|
| 写作 | William Zinsser, Barbara Minto |
| 产品 | Marty Cagan, Teresa Torres |
| 定价 | Patrick Campbell |
| 营销 | Seth Godin, April Dunford |
| 面试用户 | Rob Fitzpatrick (The Mom Test) |
| 战略 | Michael Porter, Hamilton Helmer |

---

## 二、Skill-TDD：对 skill 本身做 TDD（原 writing-skills）

### 铁律

```
没有失败测试，就不写 skill。
```

必须先看到 AI 在没有 skill 时的错误行为，然后才写 skill 来纠正。

### 🔴 RED：基线测试

在没有 skill 的情况下运行压力场景：

- AI 做了什么选择？
- 用了什么合理化借口？（逐字记录）
- 跳过了什么步骤？
- 产出的质量如何？

### 🟢 GREEN：写最小 skill

针对观察到的失败编写 skill：

- 只针对观察到的具体问题
- 不要添加"可能有用"的内容
- 包含反合理化表格
- 用相同场景重新测试

### 🔵 REFACTOR：堵漏洞

AI 找到了新的合理化借口？添加明确对策。重新测试直到防弹。

---

## 三、SKILL.md 文件结构规范

### Frontmatter

```yaml
---
name: [kebab-case 名称]
description: [何时使用——只写触发条件，不总结工作流]
---
```

### description 字段的陷阱

**关键发现：** 当 description 总结了工作流时，AI 会跳过阅读完整 skill。

- ❌ `A skill that helps you brainstorm by asking questions, proposing approaches, and creating specs`
- ✅ `Use when a new feature, product, or significant change is requested`

### skill 主体结构

1. **宣言**：让用户知道 AI 调用了什么 skill
2. **核心原则 / 铁律**：一句话级别
3. **流程步骤 / 决策树**：具体可执行
4. **反模式 / 红旗**：防止 AI 合理化绕过
5. **输出格式**：明确的交付物
6. **压力测试**：高压场景 + 常见偏差 + 纠正

---

## 四、Skill 类型

### 派发器 skill（dispatcher）

- 用途：identify + 派发给 agent workflow
- 长度：≤ 30 行
- 不含：workflow 步骤 / 模板 / 评审标准
- 示例：`skills/product/planning/SKILL.md`

### 刚性原子 skill（rigid）

- 用途：被 agent workflow 调用的原子纪律
- 长度：60-150 行
- 包含：铁律 + 违规处罚 + 反合理化表格
- 示例：`skills/engineering/tdd/SKILL.md`、`skills/engineering/debugging/SKILL.md`

### 柔性 skill（flexible）

- 用途：提供框架供 agent 适配
- 长度：80-200 行
- 包含：原则 + 可选策略 + 场景清单
- 示例：`skills/engineering/agent-dispatch/SKILL.md`（两种派发模式）

### 元 skill（meta）

- 用途：系统层规则
- 长度：不限，但需清晰结构化
- 示例：`skills/using-superopc/SKILL.md`（总则）、`skills/using-superopc/session-management/`

---

## 五、一人公司 skill 作者检查清单

- [ ] 看到了 AI 在没有 skill 时的真实错误 RED 样本？
- [ ] description 只写触发条件（<120 字符），不总结工作流？
- [ ] 判断了 skill 类型（派发器 / 刚性 / 柔性 / 元）？
- [ ] 若属于业务 workflow，是否已确认对应 agent 存在或需新建？
- [ ] 包含反模式与红旗？
- [ ] 有具体输出格式？
- [ ] 有压力测试章节？
- [ ] skill 长度合理（派发器 ≤ 30 / 原子 60-150 / 柔性 80-200）？
- [ ] 与现有 skill 不重叠（否则应合并或删除）？

---

## 关联文档

- `skills/using-superopc/SKILL.md` — 总则与 skill 体系
- `AGENTS.md` — agent 编排与 dispatcher 映射
- `CLAUDE.md` — skill-first 规则与优先级
- `references/review-rubric.md` — skill 内容审查维度
