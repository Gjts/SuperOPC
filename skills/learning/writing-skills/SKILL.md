---
name: writing-skills
description: Use when creating or improving SuperOPC skills. TDD applied to documentation — test with pressure scenarios before writing.
---

## 编写技能

**核心概念：** 编写技能就是对流程文档做 TDD。

**宣布：** "我正在使用 writing-skills 技能来创建/改进一个 SuperOPC 技能。"

## 铁律

```
没有失败测试，就不写技能。
```

必须先看到 AI 在没有技能时的错误行为，然后才写技能来纠正。

## RED-GREEN-REFACTOR for Skills

### 🔴 RED：基线测试

在没有技能的情况下运行压力场景：
- AI 做了什么选择？
- 用了什么合理化借口？（逐字记录）
- 跳过了什么步骤？
- 产出的质量如何？

### 🟢 GREEN：写最小技能

针对观察到的失败编写技能：
- 只针对观察到的具体问题
- 不要添加"可能有用"的内容
- 包含反合理化表格
- 用相同场景重新测试

### 🔵 REFACTOR：堵住漏洞

AI 找到了新的合理化借口？添加明确对策。重新测试直到防弹。

## 技能文件结构

```yaml
---
name: [kebab-case 名称]
description: [何时使用——只写触发条件，不总结工作流]
---
```

### description 字段的陷阱

**关键发现：** 当 description 总结了工作流时，AI 会跳过阅读完整技能。

- ❌ "A skill that helps you brainstorm by asking questions, proposing approaches, and creating specs"
- ✅ "Use when a new feature, product, or significant change is requested"

### 技能内容结构
1. **宣布语句**：让用户知道你在用什么技能
2. **核心原则**：一句话
3. **流程步骤**：具体的执行步骤
4. **反模式 / 红旗**：防止绕过
5. **输出格式**：明确的交付物

## 技能类型

**刚性技能**：规则必须严格遵循（TDD, debugging）
- 包含"铁律"
- 包含违规处罚（删除代码重来）
- 包含反合理化表格

**柔性技能**：原则可以适配（brainstorming, market-research）
- 提供框架而不是脚本
- 允许根据上下文调整

## 输出
一个完整的 SKILL.md 文件，通过压力测试验证。
