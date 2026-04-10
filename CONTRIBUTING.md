# Contributing to SuperOPC

感谢你考虑为 SuperOPC 贡献代码！SuperOPC 是一人公司的 AI 操作系统，我们欢迎所有形式的贡献。

## 目录

- [行为准则](#行为准则)
- [贡献方式](#贡献方式)
- [技能贡献指南](#技能贡献指南)
- [代理贡献指南](#代理贡献指南)
- [命令贡献指南](#命令贡献指南)
- [Hooks 贡献指南](#hooks-贡献指南)
- [Pull Request 流程](#pull-request-流程)
- [Commit 规范](#commit-规范)
- [开发环境](#开发环境)

---

## 行为准则

- **尊重** — 尊重每位贡献者，鼓励建设性讨论
- **包容** — 欢迎所有背景的人参与
- **务实** — 聚焦一人公司场景的实际价值
- **质量** — 宁可少而精，不要多而杂

---

## 贡献方式

### 1. 添加新技能

技能是 SuperOPC 的核心。每个技能解决一个具体问题。

### 2. 添加新代理

代理是专业角色，执行具体的工作流任务。

### 3. 添加新命令

命令是用户的入口点，以 `/opc-` 前缀开头。

### 4. 改进现有内容

- 增强技能的压力场景覆盖
- 改进代理的专业知识
- 修复错别字和格式问题
- 添加多语言翻译（中/英/日/韩/葡）

### 5. 报告问题

- 检查是否已有相同 Issue
- 提供清晰的复现步骤
- 说明你的使用场景

---

## 技能贡献指南

### 技能文件结构

每个技能是一个目录，包含一个 `SKILL.md` 文件：

```
skills/
  {category}/
    {skill-name}/
      SKILL.md
```

### 技能类别

| 类别 | 目录 | 用途 |
|------|------|------|
| 产品开发 | `skills/product/` | 从构思到交付的产品流程 |
| 工程质量 | `skills/engineering/` | 编码、测试、调试、部署 |
| 商业运营 | `skills/business/` | 定价、营销、财务、法务 |
| 市场情报 | `skills/intelligence/` | 市场研究、竞品分析、趋势追踪 |
| 学习进化 | `skills/learning/` | 技能创建、系统进化 |

### SKILL.md 模板

```markdown
---
name: skill-name
description: 一句话描述何时使用此技能。说清触发条件。
---

## 技能标题

**宣布：** "我正在使用 {skill-name} 技能。"

## 何时使用

- 触发条件 1
- 触发条件 2

## 流程

### 第一步：标题
具体指令...

### 第二步：标题
具体指令...

## 输出格式

描述此技能产出什么...

## 一人公司视角

为什么这对独立创始人特别重要...
```

### 技能设计原则

1. **单一职责** — 一个技能解决一个问题
2. **明确触发** — description 必须说清何时使用
3. **可执行** — 步骤必须具体可执行，不是泛泛的建议
4. **一人公司视角** — 考虑独立创始人的时间/资源约束
5. **压力测试** — 提供能验证技能有效性的场景


### 什么是好的技能

**好技能具备：**
- 明确的触发条件（description 字段说清何时触发）
- 具体可执行的步骤（不是"考虑 X"而是"执行 X 并输出 Y"）
- 一人公司场景的实际价值
- 与现有技能不重叠
- 压力测试场景

**避免：**
- 泛泛的建议（"注意安全"→ 应该是具体的安全检查清单）
- 太宽泛的范围（应拆分为多个技能）
- 无法验证的指令
- 与现有技能功能重叠

---

## 代理贡献指南

### 代理文件结构

```
agents/
  opc-{agent-name}.md
```

### 代理 Markdown 模板

```markdown
---
name: opc-agent-name
description: 一句话描述代理的专业角色
tools: ["Read", "Write", "Edit", "Bash", "Grep", "Glob"]
model: sonnet
---

# Agent Name

角色描述...

## 身份

- **角色**：具体角色描述
- **性格**：工作风格
- **专长**：专业领域

## 核心职责

1. 职责一
2. 职责二

## 工作流程

### 阶段一：标题
步骤...

### 阶段二：标题
步骤...

## 输出格式

描述代理产出什么格式的结果...

## 协作规则

与其他代理的协作方式...
```

### 代理命名规则

- 前缀 `opc-`（核心代理）或放在 `agents/domain/`（领域代理）
- 使用 kebab-case：`opc-security-auditor`
- 名称反映专业角色

---

## 命令贡献指南

### 命令文件结构

```
commands/
  opc/
    {command-name}.md
```

### 命令模板

```markdown
---
name: opc-command-name
description: 一句话描述此命令的用途
---

# /opc-command-name -- 命令标题

## 流程

1. **步骤一**
   - 具体操作

2. **步骤二**
   - 具体操作

## 调用技能

- 技能 1 -> 技能 2

## 输出

描述命令执行后的产出...
```

---

## Hooks 贡献指南

SuperOPC 使用 Claude Code hooks 系统实现自动化质量门控。

### Hooks 文件结构

```
hooks/
  hooks.json            # 钩子注册表
scripts/
  hooks/
    {hook-name}.js      # 钩子脚本
```

### 钩子类型

| 事件 | 触发时机 | 用途 |
|------|---------|------|
| `PreToolUse` | 工具调用前 | 拦截/警告/检查 |
| `PostToolUse` | 工具调用后 | 审计/追踪/质量检查 |
| `PreCompact` | 上下文压缩前 | 保存状态 |
| `Stop` | 响应结束时 | 批量检查/通知 |
| `SessionStart` | 新会话开始 | 加载上下文 |

### 钩子脚本规范

```python
#!/usr/bin/env python3
# hooks/{hook_name}.py
#
# 通过 stdin 接收 JSON：
#   { tool_name, tool_input, ... }
#
# 退出码：
//   0 = 通过（可附带 stdout 消息作为建议）
//   2 = 阻止（stdout 消息作为阻止原因）
//
// 原则：建议性优于强制性

const input = JSON.parse(require('fs').readFileSync(0, 'utf8'));

// 你的检查逻辑...

if (shouldWarn) {
  console.log('SuperOPC: 建议信息...');
  process.exit(0); // 建议，不阻止
}

if (shouldBlock) {
  console.log('SuperOPC: 阻止原因...');
  process.exit(2); // 阻止
}
```

### 钩子设计原则

1. **建议性优先** — 大多数钩子应该是建议而非阻止
2. **快速执行** — 钩子不应阻塞工作流超过 5 秒
3. **安全退化** — 钩子失败不应阻止正常工作
4. **可配置** — 通过环境变量或配置文件控制开关

---

## Pull Request 流程

### 提交前检查

1. **文件格式** — SKILL.md/代理/命令文件有正确的 frontmatter
2. **命名规范** — kebab-case，技能/代理/命令命名一致
3. **无重叠** — 与现有内容不重复
4. **双语** — 核心内容建议中英双语
5. **压力测试** — 技能附带至少 1 个压力场景

### 提交流程

1. **Fork** 仓库
2. **创建分支**：`git checkout -b add-skill-{name}` 或 `add-agent-{name}`
3. **添加文件** 并确保格式正确
4. **提交**：`git commit -m "feat(skills): add {skill-name}"`
5. **推送** 并创建 Pull Request

### Commit 消息格式

提交信息请优先遵循仓库根目录中的 `COMMIT_STYLE.md`。

核心要求：

- 标题采用 Conventional Commits 风格
- 正文使用三段式：
  - `概述：`
  - `逐文件详细说明：`
  - `来源引用：`
- 文件较多时，允许在 `逐文件详细说明：` 中按分类分组，分类标题格式统一为：
  - `【分类名（数量 + 来源/适配说明）】`

简化标题示例：

```
feat(skills): add {skill-name}
feat(agents): add opc-{agent-name}
feat(commands): add /opc-{command-name}
feat(hooks): add {hook-name} hook
fix(skills): improve {skill-name} trigger conditions
docs: update README with new skill
```

如提交涉及多个文件、系统结构、技能/代理/规则扩展或来源融合，请使用 `COMMIT_STYLE.md` 中的完整模板，而不是只写单行标题。

### Commit 规范

完整提交规范见仓库根目录：`COMMIT_STYLE.md`

建议以下类型严格遵循完整规范：

- `feat`
- `refactor`
- `docs`
- `perf`
- `build`
- `chore`（涉及结构、模板、规范、工具链时）

### PR 模板

```markdown
## 贡献类型
- [ ] 新技能
- [ ] 新代理
- [ ] 新命令
- [ ] 新钩子
- [ ] 改进现有内容
- [ ] 文档/翻译

## 描述
[这个贡献解决什么问题？]

## 一人公司场景
[为什么这对独立创始人有价值？]

## 测试
[你如何验证了这个贡献的有效性？]

## 检查清单
- [ ] frontmatter 格式正确（name + description）
- [ ] 文件放在正确的目录
- [ ] 与现有内容无重叠
- [ ] 经过实际场景测试
```

---

## 开发环境

### 前提条件

- Git
- Python 3.11+（运行 hooks 和 scripts）
- 任意支持的 AI 编码工具（Claude Code / Cursor / Windsurf）

### 本地设置

```bash
git clone https://github.com/user/SuperOPC.git
cd SuperOPC

# 如果使用 Claude Code，直接安装为插件
# SuperOPC 的 CLAUDE.md 会自动生效

# 运行格式转换（生成 Cursor/Windsurf 等格式）
python scripts/convert.py --tool all
```

### 目录结构

```
SuperOPC/
  .claude-plugin/     # 插件元数据
  agents/             # 专业代理
  commands/opc/       # 斜杠命令
  hooks/              # 钩子系统
    hooks.json        # 钩子注册表
  scripts/            # 工具脚本
    hooks/            # 钩子脚本
    convert.py        # 多工具格式转换
  skills/             # 技能系统（核心）
    using-superopc/   # 元技能
    product/          # 产品技能组
    engineering/      # 工程技能组
    business/         # 商业技能组
    intelligence/     # 情报技能组
    learning/         # 学习技能组
  CLAUDE.md           # 系统指令
  AGENTS.md           # 代理协调规则
  ROADMAP.md          # 路线图
```

---

## 多工具格式支持

SuperOPC 原生支持 Claude Code 格式，同时通过 `scripts/convert.py` 转换为其他工具格式：

| 工具 | 转换格式 | 输出位置 |
|------|---------|---------|
| Claude Code | SKILL.md + CLAUDE.md（原生） | 根目录 |
| Cursor | .cursor/rules/*.mdc | `integrations/cursor/` |
| Windsurf | .windsurfrules | `integrations/windsurf/` |
| Gemini CLI | skills/*/SKILL.md | `integrations/gemini-cli/` |
| OpenCode | .opencode/agents/*.md | `integrations/opencode/` |

贡献新工具格式支持时，请在 `scripts/convert.py` 中添加对应的转换函数。

---

## 问题和讨论

- **Bug 报告**：[GitHub Issues](https://github.com/user/SuperOPC/issues)
- **功能建议**：[GitHub Discussions](https://github.com/user/SuperOPC/discussions)
- **问题咨询**：[GitHub Discussions](https://github.com/user/SuperOPC/discussions)

---

**感谢你的贡献！每一个技能、代理、命令都让一人公司创始人的工作更高效。**
