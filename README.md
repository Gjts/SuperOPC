<div align="center">

# 🚀 SuperOPC

**一人公司超级操作系统 — The One-Person Company Operating System**

AI 驱动的工作流、代理和技能系统，帮助独立创始人构建、发布和增长产品。

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

[English](README_EN.md) · [中文](#中文说明)

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
git clone https://github.com/gjts/superopc.git
```

> 当前仓库是 SuperOPC 的**插件源码仓库**，尚未在 Claude Code 可识别的 marketplace 中发布，因此**不能**直接使用 ` /plugin install superopc `。
>
> 在独立的 marketplace 仓库发布并验证前，请将本仓库视为插件源码/本地开发包来使用。
>
> 未来的终端用户安装流预计为：
> ` /plugin marketplace add gjts/superopc-marketplace `
> ` /plugin install superopc@superopc-marketplace `

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
转换后的文件输出到 `integrations/<tool>/`（目录已纳入 `.gitignore`，新克隆仓库里为空，请先跑一次 `python scripts/convert.py --tool all` 生成）。`scripts/convert.py` 现在同时提供：
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

SuperOPC 内置 **13 个质量门控与学习钩子**（源自 [ECC hooks.json](https://github.com/nicobailon/everything-claude-code) 模式，v1.1+ 增加了 observe/bridge 向 v2 事件总线联动）：

### PreToolUse（工具调用前，7 个）

| 钩子 | Matcher | 功能 |
|------|---------|------|
| **block-no-verify** | Bash | 🔴 阻止 `git --no-verify` 绕过 pre-commit（唯一的强阻断钩子之一） |
| **commit-quality** | Bash | 检查 `git commit -m` 是否符合 Conventional Commits，并扫描提交消息中的疑似密钥；同时通过 `bridge.py` 发 `hook.commit_quality` 到 v2 事件总线 |
| **read-before-edit** | Edit/Write/MultiEdit | 编辑前提示先读取目标文件（建议性） |
| **doc-file-warning** | Write | 警告创建非标准路径下的文档文件 |
| **config-protection** | Edit/Write/MultiEdit | 保护 linter / formatter / test 配置文件不被弱化（建议性） |
| **prompt-injection-scan** | Edit/Write/MultiEdit | 扫描写入内容中的常见提示注入模式和不可见字符（建议性） |
| **state-file-lock** | Edit/Write/MultiEdit | 波次执行中 `.opc/STATE.md` 并行写入冲突检测（建议性） |

### PostToolUse（工具调用后，4 个）

| 钩子 | Matcher | 功能 |
|------|---------|------|
| **command-audit-log** | Bash | 追加已执行 bash 命令到 `.opc/audit.log`，供会话审查 |
| **console-log-warn** | Edit/Write/MultiEdit | 检测编辑内容中遗留的 `console.log` / `print` debug 语句 |
| **git-push-reminder** | Bash | 提醒在 git push 前先审查 diff |
| **observe** | `*`（全部） | v1.1 持续学习：把工具调用观测写到 `~/.opc/learnings/observations.jsonl`，供 `instinct_generator` 生成个性化规则 |

### Notification & Stop（2 个）

| 钩子 | 类型 | 功能 |
|------|------|------|
| **statusline** | Notification:StatusLine | 状态栏展示：模型 + 当前任务 + 目录 + 上下文使用率进度条 |
| **session-summary** | Stop | 持久化会话摘要（时间戳、工具名、会话 ID） |

### 共享支持（不注册为钩子）

`scripts/hooks/bridge.py` 和 `common.py` 是其他钩子 import 的支持库。`bridge.py` 负责把钩子事件发布到 v2 `event_bus`，供 `decision_engine` / `cruise_controller` / `notification` 消费。

钩子遵循**建议性优先**原则——大多数钩子只发出警告或提示，不会阻止正常工作流；只有 `block-no-verify` 和 `commit-quality` 检测到高风险密钥模式时会强阻断。

## 架构

```
SuperOPC/
├── skills/                    # 技能系统（v1.4.2 精简 17 个：10 派发器 + 4 原子 + 2 元层 + 1 学习）
│   ├── using-superopc/        # 🧭 元层与自主运营（5 个：1 元层 SKILL.md + 4 子技能）
│   │   ├── SKILL.md           # 总则：如何发现与调用 skill（元层）
│   │   ├── session-management/# 📡 派发 opc-session-manager（v1.4.2 升级为派发器）
│   │   ├── autonomous-ops/    # 📡 派发 opc-cruise-operator（v1.4.2 升级为派发器）
│   │   ├── workflow-modes/    # 📡 派发 opc-orchestrator 做 7 模式路由
│   │   └── developer-profile/ # 元层：8 维度开发者画像（引擎消费）
│   ├── product/               # 🚀 产品派发器（4 个）
│   │   ├── planning/          # 📡 派发 opc-planner（吸收旧 brainstorming）
│   │   ├── implementing/      # 📡 派发 opc-executor
│   │   ├── reviewing/         # 📡 派发 opc-reviewer（Quick/Standard/Deep）
│   │   └── shipping/          # 📡 派发 opc-shipper
│   ├── engineering/           # 🔧 工程（6 个：2 派发器 + 4 原子）
│   │   ├── debugging/         # 📡 派发 opc-debugger
│   │   ├── security-review/   # 📡 派发 opc-security-auditor
│   │   ├── tdd/               # 原子：RED-GREEN-REFACTOR 铁律
│   │   ├── verification-loop/ # 原子：4 层验证 + Nyquist 采样
│   │   ├── agent-dispatch/    # 原子：子代理派发（Mode A/B）
│   │   └── git-worktrees/     # 原子：隔离工作空间
│   ├── business/              # 💼 商业（1 个派发器）
│   │   └── advisory/          # 📡 派发 opc-business-advisor → 按 references/business/ 执行 20 个子活动
│   └── learning/              # 📚 学习（1 个）
│       └── continuous-learning/ # PostToolUse 观察管道 + 本能演化
├── references/                # 📖 知识库（v1.4 新层）
│   ├── business/              # 19 个一人公司 playbook（定价/验证/MVP/获客/营销/SEO/法务/财务...）
│   ├── patterns/engineering/  # 13 个技术栈 patterns（nextjs/dotnet/postgres/docker/kotlin-compose/api-design/ADR/...）
│   ├── intelligence/          # market-research / follow-builders 方法论
│   ├── security-checklist.md  # OWASP Top 10 完整清单
│   ├── review-rubric.md       # 代码审查 5 维度 + Quick/Standard/Deep
│   ├── skill-authoring.md     # skill 作者手册（合并 skill-from-masters + writing-skills）
│   ├── plan-template.md       # PLAN.md 模板
│   ├── gates.md / verification-patterns.md / anti-patterns.md / ...（其他 v0.x 参考）
├── agents/                    # 专业代理（27 个：20 core + 2 matrix + 5 domain，v1.4.2 +2）
│   ├── opc-orchestrator.md    # 全流程编排器
│   ├── opc-planner.md         # 规划专家（Phase 0-5 完整流程）
│   ├── opc-executor.md        # 执行专家
│   ├── opc-reviewer.md        # 审查专家（Quick/Standard/Deep）
│   ├── opc-shipper.md         # 发布专家
│   ├── opc-researcher.md      # 研究专家
│   ├── opc-verifier.md        # 验证专家
│   ├── opc-debugger.md        # 科学方法调试（假设-证据-排除+修复规程）
│   ├── opc-security-auditor.md # OWASP Top 10 + ASVS 审计
│   ├── opc-business-advisor.md # 一人公司商业顾问（v1.4 新增，20 个子活动）
│   ├── opc-session-manager.md # 会话连续性（v1.4.2 新增：pause/resume/progress/session-report）
│   ├── opc-cruise-operator.md # 自主运营（v1.4.2 新增：cruise/heartbeat/autonomous）
│   ├── opc-doc-writer.md      # 文档生成
│   ├── opc-doc-verifier.md    # 文档准确性验证
│   ├── opc-codebase-mapper.md # 4 维代码地图
│   ├── opc-ui-auditor.md      # 6 支柱 UI 审计
│   ├── opc-plan-checker.md    # 8 维度计划验证
│   ├── opc-assumptions-analyzer.md # 隐藏假设分析
│   ├── opc-roadmapper.md      # 产品路线图
│   ├── opc-intel-updater.md   # 代码库索引刷新
│   ├── matrix/                # 2 个专业执行代理：opc-frontend-wizard / opc-backend-architect
│   └── domain/                # 5 个按需激活领域代理：devops / seo / content / growth / pricing
├── commands/                  # 斜杠命令（25 个：16 派发器 + 6 纯只读 CLI + 3 混合低摩擦 CLI）
│   └── opc/
│       ├── opc.md             # /opc 统一自然语言入口（派发 workflow-modes）
│       ├── start.md           # /opc-start 初始化项目（派发 planning 或 workflow-modes）
│       ├── plan.md            # /opc-plan 规划功能（派发 planning）
│       ├── build.md           # /opc-build 执行开发（派发 implementing）
│       ├── review.md          # /opc-review 代码审查（派发 reviewing）
│       ├── ship.md            # /opc-ship 发布（派发 shipping）
│       ├── debug.md           # /opc-debug 调试（派发 debugging，v1.4.2 新增）
│       ├── security.md        # /opc-security 安全审计（派发 security-review，v1.4.2 新增）
│       ├── business.md        # /opc-business 商业决策（派发 business-advisory，v1.4.2 新增）
│       ├── progress.md        # /opc-progress 会话进度（派发 session-management）
│       ├── pause.md           # /opc-pause 暂停并交接（派发 session-management）
│       ├── resume.md          # /opc-resume 恢复会话（派发 session-management）
│       ├── session-report.md  # /opc-session-report 会话报告（派发 session-management）
│       ├── cruise.md          # /opc-cruise 启动巡航（派发 autonomous-ops）
│       ├── heartbeat.md       # /opc-heartbeat 查看心跳（派发 autonomous-ops）
│       ├── autonomous.md      # /opc-autonomous 有边界自主推进（派发 autonomous-ops）
│       ├── health.md          # /opc-health 质量体检（纯只读 CLI）
│       ├── dashboard.md       # /opc-dashboard 项目仪表盘（纯只读 CLI）
│       ├── stats.md           # /opc-stats 项目指标（纯只读 CLI）
│       ├── intel.md           # /opc-intel 代码库情报（纯只读 CLI，refresh 子命令走 agent）
│       ├── profile.md         # /opc-profile 开发者画像（纯只读 CLI）
│       ├── research.md        # /opc-research 研究产物索引（纯只读 CLI）
│       ├── thread.md          # /opc-thread 上下文线程（混合低摩擦 CLI）
│       ├── seed.md            # /opc-seed 想法种子（混合低摩擦 CLI）
│       └── backlog.md         # /opc-backlog 延后任务池（混合低摩擦 CLI）
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
├── templates/                 # 模板系统
│   ├── *.md / *.json          # .opc 文件模板
│   └── projects/              # 项目脚手架模板
│       ├── saas-starter/      # Next.js + Supabase + Stripe
│       ├── api-service/       # .NET 8 + PostgreSQL
│       ├── mobile-app/        # Kotlin + Jetpack Compose
│       └── landing-page/      # Next.js 静态导出营销页
├── examples/                  # 使用示例
│   ├── 01-saas-mvp-workflow/  # SaaS MVP 完整工作流
│   ├── 02-api-development/    # API 服务开发流程
│   └── 03-business-workflow/  # 商业技能运营实战
├── docs/                      # 社区文档
│   ├── building-in-public.md  # Building in Public 教程
│   ├── contributor-rewards.md # 贡献者奖励机制
│   └── community-guide.md     # 社区指南
├── CLAUDE.md                  # AI 系统指令
├── AGENTS.md                  # 代理编排规则
├── CONTRIBUTING.md            # 贡献指南
├── CODE_OF_CONDUCT.md         # 行为准则
└── .claude-plugin/            # 插件清单
```

## 快速开始

> **快速选命令：** 如果你不确定该用哪个 slash 命令，先看 **[docs/COMMAND-CHEAT-SHEET.md](docs/COMMAND-CHEAT-SHEET.md)**（一页纸决策树 + 端到端旅程 + 错误路径速查）。

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

### 6. 查看项目仪表盘（只读 CLI）
```
/opc-dashboard
```
或命令行：`python scripts/opc_dashboard.py --cwd /path/to/your/project`
汇总阶段、计划、需求、MRR、债务、下一步。这是 v1.4.2 **只读白名单命令**之一。

### 7. 查看会话进度
```
/opc-progress
```
派发 `session-management` skill → `opc-session-manager` agent，输出五段式摘要（阶段 / 最近动作 / 未完成 TODO / 验证欠债 / 唯一主下一步）。

### 8. 运行项目健康检查（只读 CLI）
```
/opc-health
```
或命令行：
```bash
python scripts/opc_health.py --cwd /path/to/your/project --repair
python scripts/opc_health.py --cwd /path/to/your/project --json
```
检查 `.opc/` 完整性、需求覆盖、SUMMARY 追踪字段、恢复文件引用，`--repair` 可补齐缺失的基础结构。只读白名单命令。

### 9. 生成会话报告
```
/opc-session-report
```
派发 `session-management` skill → `opc-session-manager` agent 的 Session-report 子场景（汇总最近会话 → STATE 快照 → 质量债务 → 写入 `.opc/session-reports/*.md`）。

### 10. 有边界自主推进
```
/opc-autonomous --from 2 --to 4
/opc-autonomous --only 3 --interactive
```
派发 `autonomous-ops` skill → `opc-cruise-operator` agent。**进入前必须通过 Anti-Build-Trap 硬门**（validate-idea + find-community 证据）。在明确窗口内连续推进，并在 blocker、验证欠债或人工检查点处停下。

### 11. 暂停并恢复工作
```
/opc-pause --note "今天先停在这里"
/opc-resume
```
`/opc-pause` 派发 `session-management` skill 写入 `.opc/HANDOFF.json` 并更新 `STATE.md` 连续性字段；`/opc-resume` 在新会话中重建上下文并推荐**唯一**一个主下一步。

### 12. 管理上下文线程 / 种子 / backlog（混合路径，见下文注意事项）
```
/opc-thread pricing-page-copy
/opc-seed "viral referral loop" --trigger "当激活率停滞时"
/opc-backlog "整理 onboarding 文案" --note "等本阶段结束后再做"
```
三个命令的"**列出**"模式是纯只读（白名单）；"**创建**"模式会写入 `.opc/threads/`、`.opc/seeds/`、`.opc/todos/`，此时应优先走 `/opc` 或 `/opc-plan` 走 agent 工作流产出更高质量的条目。直接 CLI 创建仅适合"我只是想快速记一条"的场景。

### 13. 导出结构化指标（只读 CLI）
```
/opc-stats
```
或命令行：`python scripts/opc_stats.py --cwd /path/to/your/project`
输出 JSON，适合日报、CI 或外部面板消费。只读白名单命令。

### 14. 启动巡航 / 查看心跳
```
/opc-cruise --mode watch --hours 2
/opc-heartbeat
```
`/opc-cruise` 启动自主运营循环（watch / assist / cruise 三档权限），`/opc-heartbeat` 只读查看当前状态、最近决策、异常信号。**Cruise 永远有时限**（`--hours` 必填或默认），无边界模式会被拒绝。

### 15. 调试 / 安全审计 / 商业决策
```
/opc-debug "测试 foo/test_login.py::test_oauth 失败"
/opc-security app/api/
/opc-business "自由职业者发票 SaaS 怎么定价"
```
分别派发 `debugging` / `security-review` / `business-advisory` skill。`business-advisory` 自带 **Anti-Build-Trap 硬门**：没有 validate-idea + find-community 证据时拒绝进入编码阶段。

---

> **关于 slash 命令 vs Python 脚本：** v1.4.2 起，所有涉及 agent workflow 的命令必须走 slash 入口
> （`/opc-xxx`），它们会派发对应的 dispatcher skill。**只读**命令（`/opc-health` `/opc-dashboard`
> `/opc-stats` `/opc-intel` `/opc-profile` `/opc-thread` `/opc-seed` `/opc-backlog` `/opc-research`）
> 允许直接调 Python 脚本作为等价替代。完整白名单规则见 `AGENTS.md` §Read-only CLI 白名单例外。

- `references/session-management.md` — pause / resume / progress / report 生命周期与冲突规则
- `references/workflow-modes.md` — autonomous / fast / quick / discuss / explore / do / next 边界
- `references/context-threads.md` — thread / seed / backlog 的存储边界与升级路径
- `references/session-workflows.md` — progress / pause / resume / report 生命周期（兼容参考）
- `references/handoff-format.md` — `.opc/HANDOFF.json` 交接格式（兼容参考）
- `templates/handoff.json` — 恢复快照模板

## 核心工作流

### 产品开发流水线
```
planning → implementing → reviewing → shipping
(澄清+方案+规划) (执行+TDD)    (审查)      (发布)
```

### 商业决策流水线
```
business-advisory → references/business/* → domain agents
(识别子活动+Anti-Build-Trap) (方法论执行)   (pricing/seo/content/growth)
```

### 质量保证
```
TDD (先写测试) + debugging (根因分析) + reviewing (五维度审查) + verifier (目标反向验证)
```

## 技能一览（v1.4.2）

SuperOPC v1.4 起严格执行 **skill-dispatcher / agent-workflow** 契约：知识库内容已下沉到 `references/`，skill 空间只保留 17 个核心技能。

| 类别 | 技能数 | 技能列表 |
|------|--------|---------|
| 🚀 产品派发器 | 4 | planning / implementing / reviewing / shipping |
| 🔧 工程派发器 | 2 | debugging / security-review |
| 💼 商业派发器 | 1 | business-advisory |
| 🧭 自主/会话派发器 | 3 | workflow-modes / session-management / autonomous-ops（v1.4.2 升级）|
| ⚙️ 原子技能 | 4 | tdd / verification-loop / agent-dispatch / git-worktrees |
| 🤖 元层 | 2 | using-superopc/SKILL.md / developer-profile |
| 📚 学习 | 1 | continuous-learning |
| **总计** | **17** | **10 派发器 + 4 原子 + 2 元层 + 1 学习** |

> **为什么不是 51？** v0.x 曾有 51 个 skill，但其中大多数是知识库文档（技术栈 patterns / 商业 playbooks）。
> v1.4 将它们下沉到 `references/`（由 agent workflow 按需引用），skill 只留真正驱动行为的派发器和不可被其他技能取代的原子规则。详见 `CHANGELOG.md` [1.4.0]。

## 设计原则

1. **技能优先** — 有适用技能就必须用，哪怕只有 1% 的可能
2. **TDD 铁律** — 没有失败测试就不写生产代码
3. **商业思维** — 每个技术决策都考虑 ROI
4. **极简主义** — 最小化复杂度、依赖、运营成本
5. **持续进化** — 系统从每次交互中学习和改进

## 路线图

完整变更记录见 **[CHANGELOG.md](CHANGELOG.md)**；未来规划见 **[ROADMAP.md](ROADMAP.md)**。

| 阶段 | 版本 | 主题 | 状态 |
|------|------|------|------|
| **基础** | v0.1.0 – v0.5.0 | 骨架→Hooks/Rules→代理扩展→状态管理→工程技能 | ✅ 完成 |
| **深化** | v0.6.0 – v1.0.0 | 商业技能→多运行时→会话管理→质量保证→正式发布 | ✅ 完成 |
| **智能** | v1.1.0 | 开发者画像+全局学习 | ✅ 完成 |
| | v1.2.0 | CLI 工具层 (`bin/opc-tools`) | ✅ 完成 |
| | v1.3.0 | Dispatcher 契约 + references/ 层 | ✅ 完成 |
| | v1.4.0 | Skill 精简到 17 个，新增 business-advisor | ✅ 完成 |
| | v1.4.1 | Skill Registry + Intent Router（ADR-0001/0002/0003） | ✅ 完成 |
| | v1.4.2 | 命令契约封堵 + cruise 真派发（ADR-0004） | ✅ 完成 |
| **待定** | v1.5.0+ | 高级调试 / 工作流引擎 / 国际化 / SDK | 📋 计划中 |
| | v2.0.0 | 超级一人公司 OS | 🎯 终极目标 |

> ROADMAP.md 中早期为 v1.1-v2.0 所规划的内容（CLI / 安全 / 领域代理 192 库 / 调试取证等）部分已在 v1.4
> 中以更精简的形式交付（花名已重新划分），但部分高阶功能（取证 / 工作流 DSL / i18n / 企业级）仍待定。

## 贡献

欢迎贡献！你可以：
- 🐛 提交 Bug 报告
- 💡 提出新技能建议
- 🔧 改进现有技能
- 📝 完善文档
- 🌐 添加多语言支持

提交信息规范：`feat/fix/docs(scope): 简述`，body 按模块分类列出文件和关键配置项。

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

SuperOPC（超级一人公司操作系统）是一个 AI 驱动的开源工具，专为独立创始人设计。它融合了 9 个顶级开源项目的精华，提供（v1.4.2 当前状态）：

- **17 个 AI 技能**：10 派发器（planning / implementing / reviewing / shipping / debugging / security-review / business-advisory / workflow-modes / session-management / autonomous-ops）+ 4 原子（tdd / verification-loop / agent-dispatch / git-worktrees）+ 2 元层 + 1 学习
- **27 个专业代理**：20 core（v1.4.2 +2：opc-session-manager / opc-cruise-operator）+ 2 matrix（frontend-wizard / backend-architect）+ 5 domain（devops / seo / content / growth / pricing）
- **25 个斜杠命令**：16 派发器命令 + 6 纯只读 CLI（/opc-health /opc-dashboard /opc-stats /opc-intel /opc-profile /opc-research）+ 3 混合低摩擦 CLI（/opc-thread /opc-seed /opc-backlog）
- **200+ references/**：技术栈 patterns / 商业 playbooks / rubric / checklist，由 agent workflow 按子活动引用
- **4 个项目模板**：SaaS / API 服务 / 移动应用 / 营销页，开箱即用
- **11 个 AI 工具适配**：Claude Code / Cursor / Windsurf / Copilot / Gemini CLI / OpenCode / Codex / Trae / Cline / Augment / OpenClaw

**理念：** 你是一个人，但有了 SuperOPC，你拥有一个 AI 团队。

</div>
