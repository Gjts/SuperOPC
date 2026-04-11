<div align="center">

# 🚀 SuperOPC

**一人公司超级操作系统 — The One-Person Company Operating System**

AI 驱动的工作流、代理和技能系统，帮助独立创始人构建、发布和增长产品。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

**English** · [中文](#中文说明)

</div>

---

## 为什么

一人公司创始人同时是 CEO、CTO、设计师、营销、客服。你不需要 50 人的企业工具，你需要一个**超级工具**把所有这些角色统一在一个系统里。

SuperOPC 融合了开源社区最优秀的 AI 工程实践：

| 来源 | 贡献 |
|------|------|
| [Superpowers](https://github.com/obra/superpowers) | 技能系统、TDD 铁律、系统调试、Git Worktree |
| [Get Shit Done](https://github.com/gsd-build/get-shit-done) | 命令系统、波次执行、代理编排、验证器 |
| [Minimalist Entrepreneur Skills](https://github.com/slavingia/skills) | 10 个极简创业技能 |
| [last30days](https://github.com/zarazhangrui/last30days-skill) | 多源市场研究引擎 |
| [Follow Builders](https://github.com/zarazhangrui/follow-builders) | 建造者情报追踪 |
| [Everything Claude Code](https://github.com/nicobailon/everything-claude-code) | 安装系统、持续学习、代理委托 |
| [skill-from-masters](https://github.com/zarazhangrui/skill-from-masters) | 从专家学习方法论 |
| [agency-agents](https://github.com/agency-agents/agency-agents) | 专业 AI 代理定义 |
| [Claude Code Best Practice](https://github.com/anthropics/claude-code-best-practice) | 工作流编排、钩子系统 |

## 安装

### Claude Code
```bash
git clone https://github.com/gjts/superopc.git ~/.claude/plugins/superopc
```

然后在 Claude Code 中：
```
/plugin install superopc
```

### 多运行时导出（Claude Code / Cursor / Windsurf / Copilot / Gemini CLI / OpenCode / Codex / Trae / Cline / Augment / OpenClaw）
```bash
git clone https://github.com/gjts/superopc.git
cd superopc
python scripts/convert.py --tool claude-code  # 导出 Claude Code 原生包
python scripts/convert.py --tool cursor       # 生成 Cursor rules
python scripts/convert.py --tool copilot      # 生成 GitHub Copilot instructions
python scripts/convert.py --tool codex        # 生成 Codex agents/commands/skills
python scripts/convert.py --tool augment      # 生成 Augment rules
python scripts/convert.py --tool auto         # 按环境标记自动选择运行时
python scripts/convert.py --tool all          # 一键生成全部导出
```

SuperOPC 当前支持 **Claude Code 原生格式**，并内置 **11 个运行时导出目标**：Claude Code、Cursor、Windsurf、Copilot、Gemini CLI、OpenCode、Codex、Trae、Cline、Augment Code、OpenClaw。
转换后的文件输出到 `integrations/<tool>/`。`scripts/convert.py` 现在同时提供：
- **运行时注册表**：统一维护每个目标运行时的目录、frontmatter 和输出布局
- **工具名映射**：把 Claude Code 工具术语转换成目标运行时可理解的名称
- **钩子事件映射**：为每个导出生成 `HOOKS.md` + `runtime-map.json`
- **自动检测**：`--tool auto` / `--detect` 根据常见配置目录建议导出目标

### MCP 服务器模板
SuperOPC 提供常用 MCP 模板，位于 `mcp-configs/mcp-servers.json`：
- `context7` — 实时文档查询
- `supabase` — Supabase 数据库 / 项目操作
- `sequential-thinking` — 分步推理
- `playwright` — 浏览器自动化 / E2E 验证

使用方式：复制你需要的条目到目标运行时的 MCP 配置文件，例如项目级 `.mcp.json` 或运行时自己的用户级配置文件，然后替换占位符（如 `YOUR_PROJECT_REF`、`YOUR_SUPABASE_ACCESS_TOKEN_HERE`）。仓库根目录也提供了一个最小默认示例 `.mcp.json`，便于直接启用这 4 个服务器。

## 钩子系统

SuperOPC 内置质量门控钩子（源自 [ECC hooks.json](https://github.com/nicobailon/everything-claude-code) 模式）：

| 钩子 | 类型 | 功能 |
|------|------|------|
| **block-no-verify** | PreToolUse | 阻止 `git --no-verify` 绕过 pre-commit |
| **commit-quality** | PreToolUse | 检查 `git commit -m` 是否符合 Conventional Commits，并扫描提交消息中的疑似密钥 |
| **read-before-edit** | PreToolUse | 编辑前提示先读取目标文件（建议性提醒，不跟踪真实读取状态） |
| **config-protection** | PreToolUse | 保护 linter / formatter 配置不被轻易削弱 |
| **prompt-injection-scan** | PreToolUse | 扫描写入内容中的常见提示注入模式（建议性） |
| **command-audit-log** | PostToolUse | 记录命令审计日志到 `.opc/audit.log` |
| **console-log-warn** | PostToolUse | 检测编辑内容中的常见 debug 语句并提醒清理 |
| **session-summary** | Stop | 持久化基础会话摘要（时间戳、工具名、会话 ID） |

钩子遵循**建议性优先**原则——大多数钩子只发出警告或提示，不会阻止正常工作流；只有 `--no-verify` 和提交消息中的高风险密钥模式会被阻止。

## 架构

```
SuperOPC/
├── skills/                    # 技能系统（核心）
│   ├── using-superopc/        # 元技能：如何使用系统
│   ├── product/               # 🚀 产品开发
│   │   ├── brainstorming/     # 头脑风暴 → 设计方案
│   │   ├── planning/          # 计划分解 → PLAN.md
│   │   ├── implementing/      # 子代理执行 + TDD
│   │   ├── reviewing/         # 五维度代码审查
│   │   └── shipping/          # 发布 → 合并/PR
│   ├── engineering/           # 🔧 工程质量
│   │   ├── tdd/               # RED-GREEN-REFACTOR 铁律
│   │   ├── debugging/         # 四阶段根因分析
│   │   ├── git-worktrees/     # 隔离工作空间
│   │   └── parallel-agents/   # 波次并行执行引擎
│   ├── business/              # 💼 商业运营
│   │   ├── find-community/    # 找到你的社区
│   │   ├── validate-idea/     # 验证商业想法
│   │   ├── mvp/               # 最小可行产品
│   │   ├── processize/        # 先手动后自动
│   │   ├── first-customers/   # 找前 100 个客户
│   │   ├── pricing/           # 定价策略
│   │   ├── legal-basics/      # 法务基础与合规边界
│   │   ├── finance-ops/       # 财务运营与 MRR / Burn / Runway
│   │   ├── investor-materials/# 融资材料
│   │   ├── product-lens/      # 产品视角审查
│   │   ├── seo/               # 搜索增长
│   │   ├── content-engine/    # 内容引擎
│   │   ├── brand-voice/       # 品牌语调
│   │   ├── user-interview/    # The Mom Test 访谈
│   │   ├── marketing-plan/    # 内容营销
│   │   ├── grow-sustainably/  # 可持续增长
│   │   ├── company-values/    # 公司价值观
│   │   └── minimalist-review/ # 极简审查
│   ├── intelligence/          # 🔍 市场情报
│   │   ├── market-research/   # 多源市场调研
│   │   └── follow-builders/   # 建造者追踪
│   └── learning/              # 📚 学习进化
│       ├── skill-from-masters/# 从大师学习
│       ├── writing-skills/    # 创建新技能
│       └── continuous-learning/# 持续改进
├── agents/                    # 专业代理（15 个）
│   ├── opc-orchestrator.md    # 全流程编排器
│   ├── opc-planner.md         # 规划专家
│   ├── opc-executor.md        # 执行专家
│   ├── opc-reviewer.md        # 审查专家
│   ├── opc-researcher.md      # 研究专家
│   ├── opc-verifier.md        # 验证专家
│   ├── opc-debugger.md        # 科学方法调试（假设-证据-排除）
│   ├── opc-security-auditor.md # OWASP 安全审计
│   ├── opc-doc-writer.md      # 文档生成
│   ├── opc-doc-verifier.md    # 文档准确性验证
│   ├── opc-codebase-mapper.md # 4 维代码地图
│   ├── opc-ui-auditor.md      # 6 支柱 UI 审计
│   ├── opc-plan-checker.md    # 8 维度计划验证
│   ├── opc-assumptions-analyzer.md # 隐藏假设分析
│   └── opc-roadmapper.md      # 产品路线图
├── commands/                  # 斜杠命令
│   └── opc/
│       ├── start.md           # /opc-start 初始化项目
│       ├── plan.md            # /opc-plan 规划功能
│       ├── build.md           # /opc-build 执行开发
│       ├── research.md        # /opc-research 市场研究
│       ├── dashboard.md       # /opc-dashboard 项目仪表盘
│       ├── stats.md           # /opc-stats 项目指标
│       ├── progress.md        # /opc-progress 会话进度
│       ├── pause.md           # /opc-pause 暂停并交接
│       ├── resume.md          # /opc-resume 恢复会话
│       ├── session-report.md  # /opc-session-report 会话报告
│       ├── ship.md            # /opc-ship 发布
│       ├── quick.md           # /opc-quick 快速任务
│       ├── review.md          # /opc-review 代码审查
│       ├── next.md            # /opc-next 推荐下一步
│       ├── health.md          # /opc-health 质量与目录体检
│       ├── autonomous.md      # /opc-autonomous 有边界自主推进
│       ├── fast.md            # /opc-fast 微任务执行
│       ├── discuss.md         # /opc-discuss 纯讨论模式
│       ├── explore.md         # /opc-explore 苏格拉底式探索
│       ├── thread.md          # /opc-thread 上下文线程
│       ├── seed.md            # /opc-seed 想法种子
│       ├── backlog.md         # /opc-backlog 延后任务池
│       └── do.md              # /opc-do 自然语言路由
├── hooks/                     # 钩子系统（质量门控）
│   └── hooks.json             # 钩子注册表（ECC 模式）
├── mcp-configs/               # MCP 模板（Context7/Supabase/Sequential Thinking/Playwright）
│   └── mcp-servers.json       # 可复制到运行时配置的 MCP 条目
├── rules/                     # 编码规则系统（ECC 模式）
│   ├── common/                # 通用规则（5 文件）
│   ├── typescript/            # TypeScript/Next.js 规则
│   ├── csharp/                # C#/.NET 8 规则
│   ├── python/                # Python 规则
│   └── kotlin/                # Kotlin / Android 规则
├── references/                # 引用文档（GSD 模式）
│   ├── gates.md               # 4 种门控分类
│   ├── verification-patterns.md # 验证模式
│   ├── anti-patterns.md       # 反模式检测
│   ├── context-budget.md      # 上下文预算
│   ├── tdd.md                 # TDD 参考
│   ├── git-integration.md     # Git 集成
│   ├── session-management.md  # 会话管理规则
│   ├── workflow-modes.md      # 工作流模式边界
│   ├── context-threads.md     # 线程 / 种子 / backlog 边界
│   ├── session-workflows.md   # 会话工作流参考
│   └── handoff-format.md      # HANDOFF.json 格式
├── scripts/                   # 工具脚本
│   ├── hooks/                 # Python 钩子脚本实现
│   ├── convert.py             # 多工具格式转换
│   ├── opc_dashboard.py       # .opc 项目仪表盘
│   ├── opc_stats.py           # .opc 结构化指标
│   ├── opc_workflow.py        # 会话/下一步共享工作流引擎
│   ├── opc_progress.py        # .opc 会话进度
│   ├── opc_pause.py           # 写入 HANDOFF.json
│   ├── opc_resume.py          # 从 handoff 恢复
│   ├── opc_session_report.py  # 聚合会话报告
│   ├── opc_next.py            # 推荐下一步
│   ├── opc_health.py          # 目录与质量体检入口
│   ├── opc_quality.py         # 共享质量检查/修复引擎
│   ├── opc_autonomous.py      # 有边界自主推进
│   ├── opc_context.py         # 线程 / 种子 / backlog 共享引擎
│   ├── opc_thread.py          # .opc 上下文线程
│   ├── opc_seed.py            # .opc 想法种子
│   ├── opc_backlog.py         # .opc 延后任务池
│   └── opc_insights.py        # 仪表盘 / 指标解析
├── CLAUDE.md                  # AI 系统指令
├── AGENTS.md                  # 代理编排规则
├── CONTRIBUTING.md            # 贡献指南
└── .claude-plugin/            # 插件清单
```

## 快速开始

### 1. 初始化项目
```
/opc-start
```
回答几个问题，SuperOPC 会创建项目结构。

### 2. 规划功能
```
/opc-plan 用户登录系统
```
AI 会：设计 2-3 个方案 → 你选一个 → 生成实施计划

### 3. 开发
```
/opc-build
```
AI 会：逐任务 TDD 执行 → 双阶段审查 → 原子提交

### 4. 发布
```
/opc-ship
```
验证测试 → 合并/PR → 清理

### 5. 商业决策
```
/opc-research AI 写作市场
```
多源调研 → 竞品分析 → 行动建议

### 6. 查看项目仪表盘
```bash
python scripts/opc_dashboard.py --cwd /path/to/your/project
```
汇总阶段、计划、需求、MRR、债务、下一步。

### 7. 查看会话进度
```bash
python scripts/opc_progress.py --cwd /path/to/your/project
```
查看当前位置、主下一步、完成度与验证欠债。

### 8. 运行项目健康检查
```bash
python scripts/opc_health.py --cwd /path/to/your/project
python scripts/opc_health.py --cwd /path/to/your/project --repair
python scripts/opc_health.py --cwd /path/to/your/project --json
```
检查 `.opc/` 完整性、需求覆盖、SUMMARY 追踪字段、恢复文件引用，并可补齐缺失的基础结构。

### 9. 生成会话报告
```bash
python scripts/opc_session_report.py --cwd /path/to/your/project
```
汇总最近会话、handoff、阻塞和恢复建议。

### 10. 有边界自主推进
```bash
python scripts/opc_autonomous.py --cwd /path/to/your/project --from 2 --to 4
python scripts/opc_autonomous.py --cwd /path/to/your/project --only 3 --interactive
```
在明确窗口内连续推进，并在 blocker、验证欠债或人工检查点处停下。

### 11. 暂停并恢复工作
```bash
python scripts/opc_pause.py --cwd /path/to/your/project --note "今天先停在这里"
python scripts/opc_resume.py --cwd /path/to/your/project
```
将恢复快照写入 `.opc/HANDOFF.json`，并在新会话中恢复上下文。

### 12. 管理上下文线程 / 种子 / backlog
```bash
python scripts/opc_thread.py --cwd /path/to/your/project "pricing-page-copy"
python scripts/opc_seed.py --cwd /path/to/your/project "viral referral loop" --trigger "当激活率停滞时"
python scripts/opc_backlog.py --cwd /path/to/your/project "整理 onboarding 文案" --note "等本阶段结束后再做"
```
把长期上下文写入 `.opc/threads/`、把未来想法写入 `.opc/seeds/`，并把延后可执行任务写入 `.opc/todos/`。

### 13. 导出结构化指标
```bash
python scripts/opc_stats.py --cwd /path/to/your/project
```
输出 JSON，适合日报、CI 或外部面板消费。

- `references/session-management.md` — pause / resume / progress / report 生命周期与冲突规则
- `references/workflow-modes.md` — autonomous / fast / quick / discuss / explore / do / next 边界
- `references/context-threads.md` — thread / seed / backlog 的存储边界与升级路径
- `references/session-workflows.md` — progress / pause / resume / report 生命周期（兼容参考）
- `references/handoff-format.md` — `.opc/HANDOFF.json` 交接格式（兼容参考）
- `templates/handoff.json` — 恢复快照模板

## 核心工作流

### 产品开发流水线
```
brainstorming → planning → implementing → reviewing → shipping
   (设计)        (规划)      (执行+TDD)    (审查)      (发布)
```

### 商业决策流水线
```
find-community → validate-idea → mvp → first-customers → pricing → grow
  (找社区)        (验证想法)    (MVP)   (获客)          (定价)   (增长)
```

### 质量保证
```
TDD (先写测试) + debugging (根因分析) + reviewing (五维度审查) + verifier (目标反向验证)
```

## 技能一览

| 类别 | 技能数 | 核心理念 |
|------|--------|---------|
| 产品开发 | 5 | brainstorm → plan → implement → review → ship |
| 工程质量 | 20 | TDD 铁律 + 调试 + 并行执行 + 工程模式库 |
| 商业运营 | 18 | 极简创业 + 财务 / 法务 / 内容 / SEO / 用户访谈 |
| 市场情报 | 2 | 多源调研 + 建造者追踪 |
| 学习进化 | 3 | 从大师学习 + 创建技能 + 持续改进 |
| 元技能 | 3 | 如何在项目里正确使用 SuperOPC |
| **总计** | **51** | |

## 设计原则

1. **技能优先** — 有适用技能就必须用，哪怕只有 1% 的可能
2. **TDD 铁律** — 没有失败测试就不写生产代码
3. **商业思维** — 每个技术决策都考虑 ROI
4. **极简主义** — 最小化复杂度、依赖、运营成本
5. **持续进化** — 系统从每次交互中学习和改进

## 路线图

查看完整的产品演进计划：**[ROADMAP.md](ROADMAP.md)**（融合 7 个来源项目，350+ 文件规划）

| 阶段 | 版本 | 主题 | 状态 |
|------|------|------|------|
| **基础** | v0.1.0 | 骨架搭建（24技能+6代理+7命令） | ✅ 完成 |
| | v0.2.0 | Hooks + Rules + 引用系统 | ✅ 完成 |
| | v0.3.0 | 代理扩展+波次执行（6→15代理+并行引擎） | ✅ 完成 |
| | v0.4.0 | 状态管理+文件系统（.opc/） | ✅ 完成 |
| | v0.5.0 | 工程技能深化（4→19） | ✅ 完成 |
| **深化** | v0.6.0 | 商业技能+仪表盘 | ✅ 完成 |
| | v0.7.0 | 多运行时适配+MCP（Claude Code + 10 个导出运行时） | ✅ 完成 |
| | v0.8.0 | 会话管理+高级工作流 | ✅ 完成 |
| | v0.9.0 | 质量保证体系 | ✅ 完成 |
| | v1.0.0 | 正式开源发布 | 🎯 里程碑 |
| **智能** | v1.1.0 | 开发者画像+全局学习 | 📋 计划中 |
| | v1.2.0 | CLI 工具层 | 📋 计划中 |
| | v1.3.0 | 安全强化 | 📋 计划中 |
| | v1.4.0 | 领域代理库（192代理精选） | 📋 计划中 |
| | v1.5.0 | 高级调试+取证 | 📋 计划中 |
| **平台** | v1.6.0 | 工作流引擎 | 📋 计划中 |
| | v1.7.0 | 国际化（5语言） | 📋 计划中 |
| | v1.8.0 | 企业级功能 | 📋 计划中 |
| | v1.9.0 | SDK+可编程接口 | 📋 计划中 |
| | v2.0.0 | 超级一人公司 OS | 🎯 终极目标 |

## 贡献

欢迎贡献！你可以：
- 🐛 提交 Bug 报告
- 💡 提出新技能建议
- 🔧 改进现有技能
- 📝 完善文档
- 🌐 添加多语言支持

提交信息规范请参考 [COMMIT_STYLE.md](COMMIT_STYLE.md)。

## 致谢

SuperOPC 站在巨人的肩膀上。感谢所有开源项目的作者：
- Jesse Vincent (Superpowers)
- TÂCHES (Get Shit Done)
- Sahil Lavingia (Minimalist Entrepreneur Skills)
- Nico Bailon (Everything Claude Code)
- 以及所有贡献者

## License

[MIT](LICENSE)

---

<div id="中文说明">

## 中文说明

SuperOPC（超级一人公司操作系统）是一个 AI 驱动的开源工具，专为独立创始人设计。它融合了 9 个顶级开源项目的精华，提供：

- **51 个 AI 技能**：覆盖产品开发、工程质量、商业运营、市场情报、学习进化
- **15 个专业代理**：编排器、规划师、执行者、审查员、调试器、安全审计、UI 审计、文档写作等
- **22 个斜杠命令**：覆盖规划、执行、发布、状态查看、会话恢复、工作流模式与自然语言路由

**理念：** 你是一个人，但有了 SuperOPC，你拥有一个 AI 团队。

</div>
