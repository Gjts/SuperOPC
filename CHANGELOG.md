# Changelog

所有 SuperOPC 的显著变更记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.7.0] - 开发中

### 新增
- **MCP 模板层** — `mcp-configs/mcp-servers.json` + `.mcp.json`
  - 提供 `context7`、`supabase`、`sequential-thinking`、`playwright` 四个可复用 MCP 条目
  - 增加最小默认 `.mcp.json` 示例，便于直接启用这 4 个服务器
- **11 运行时导出注册表** — `scripts/convert.py`
  - 新增 `claude-code`、`copilot`、`codex`、`trae`、`cline`、`augment` 导出支持
  - 保留既有 `cursor`、`windsurf`、`gemini-cli`、`opencode`、`openclaw` 兼容输出
- **运行时元数据生成**
  - 每个导出运行时生成 `runtime-map.json`
  - 每个导出运行时生成 `HOOKS.md`，说明 Claude Code hook 事件如何映射或降级
- **运行时自动检测**
  - `python scripts/convert.py --tool auto`
  - `python scripts/convert.py --detect`

### 变更
- 重构 `scripts/convert.py` 为运行时注册表 + frontmatter / 正文 / 工具名映射结构
- 更新 `README.md` 添加 10+ 运行时导出说明、自动检测、hook 映射说明和最小 `.mcp.json` 用法
- 更新 `CONTRIBUTING.md` 修正 hooks Python 示例，并补充多运行时扩展规则
- 更新 `ROADMAP.md` 标记 v0.7.0 的 MCP、运行时适配、convert 脚本与检测映射子项已完成
- 更新 `.claude-plugin/plugin.json` 到 `0.7.0`


## [0.6.0] - 完成

### 新增
- **8 个商业技能** — `skills/business/` 从 10 扩展到 18
  - `legal-basics/` — 名称/商标/合同/隐私/GDPR 最小风险盘点
  - `finance-ops/` — 记账、发票、MRR、Burn、Runway 周月节奏
  - `investor-materials/` — deck、memo、KPI snapshot、data room
  - `product-lens/` — 激活路径、留存锚点、PMF 信号审查
  - `seo/` — 搜索意图、内容集群、money pages
  - `content-engine/` — 输入→生产→分发→复用内容系统
  - `brand-voice/` — 品牌语调支柱、禁用词、场景化写作
  - `user-interview/` — The Mom Test 访谈提纲与证据分级
- **2 个仪表盘命令** — `commands/opc/dashboard.md` + `commands/opc/stats.md`
- **项目指标脚本** — `scripts/opc_dashboard.py` + `scripts/opc_stats.py`
  - 自动读取 `.opc/PROJECT.md` / `REQUIREMENTS.md` / `ROADMAP.md` / `STATE.md`
  - 输出阶段、计划、需求、债务、MRR、Git 指标
  - 支持 `--cwd` 指向目标项目
- **共享指标解析模块** — `scripts/opc_insights.py`

### 变更
- 更新 `templates/state.md`，新增“商业指标”区块，供仪表盘读取
- 更新 `scripts/convert.py`，Gemini CLI 扩展版本号改为读取插件 manifest，避免漂移
- 将主工具脚本迁移并统一到 Python：`scripts/convert.py` + `scripts/hooks/*.py` 作为当前主实现，替代早期 JavaScript 版本
- 更新 `.claude-plugin/plugin.json` 到 `0.6.0`，并注册完整 15 代理
- 更新 `README.md`、`ROADMAP.md` 标记 v0.6.0 已完成

---

## [0.5.0] - 完成

### 新增
- **15 个工程技能** — `skills/engineering/` 从 4 扩展到 19
  - **通用工程（11 个）：**
    - `api-design/` — RESTful + GraphQL API 设计（URL 结构、状态码、分页、版本策略）
    - `database-migrations/` — 迁移生命周期 + ORM drift 检测 + 零停机模式
    - `docker-patterns/` — 多阶段构建 + 安全加固 + docker-compose 开发环境
    - `deployment-patterns/` — 蓝绿/金丝雀/滚动部署 + CI/CD 流水线 + 回滚策略
    - `security-review/` — OWASP Top 10 完整检查清单 + 审查报告格式
    - `e2e-testing/` — Playwright 配置 + Page Object + Fixtures + 视觉回归
    - `architecture-decision-records/` — ADR 格式 + 索引 + 生命周期
    - `frontend-patterns/` — React/Next.js 组件设计 + 状态管理 + 表单 + 性能
    - `backend-patterns/` — 分层架构 + Repository/Service + N+1 + 缓存 + 错误处理
    - `verification-loop/` — 四层验证 + Nyquist 采样 + 节点修复
    - `codebase-onboarding/` — 五阶段棕地映射 + CLAUDE.md 生成
    - `code-review-pipeline/` — Quick/Standard/Deep 三级审查
  - **技术栈专属（4 个）：**
    - `nextjs-patterns/` — Server Components + Server Actions + Route Handlers + Middleware
    - `dotnet-patterns/` — Minimal API + EF Core + FluentValidation + DI
    - `postgres-patterns/` — 索引策略 + 查询优化 + RLS + 连接池
    - `kotlin-compose/` — State Hoisting + ViewModel + Navigation + Material 3

### 变更
- 更新 `ROADMAP.md` 标记 v0.5.0 已完成
- 更新 `CHANGELOG.md` 添加 v0.5.0 变更记录
- `skills/engineering/` 总技能数：19（基础 4 + 通用 11 + 技术栈 4）

---

## [0.4.0] - 完成

### 新增
- **配置系统** — `templates/config.json`
  - 工作流开关：research, plan_check, verifier, nyquist, node_repair, code_review
  - 模型配置：quality / balanced / budget / inherit
  - 粒度控制：coarse(3-5) / standard(5-8) / fine(8-12)
  - Git 策略：none / phase / milestone
  - 并行执行配置：max_concurrent_agents, min_plans_for_parallel
  - 门控配置：confirm_project, confirm_roadmap, confirm_plan, confirm_transition
  - 安全策略：always_confirm_destructive, always_confirm_external_services
- **模板系统** — `templates/` 目录（7 个模板）
  - `project.md` — 项目愿景、核心价值、需求分类、约束、关键决策
  - `requirements.md` — 可检查需求（v1/v2/超范围）+ 可追溯性矩阵
  - `state.md` — 活状态：位置、决策、阻塞、性能指标、会话连续性
  - `roadmap.md` — 阶段路线图（依赖、成功标准、进度追踪）
  - `phase-prompt.md` — 可执行阶段计划（波次分配、验收标准、检查点）
  - `summary.md` — 阶段摘要（依赖图、技术追踪、需求完成）
  - `debug.md` — 调试会话（科学方法：假设→证据→排除→解决）

### 变更
- 更新 `ROADMAP.md` 标记 v0.4.0 已完成
- 更新 `CHANGELOG.md` 添加 v0.4.0 变更记录

---

## [0.3.0] - 完成

### 新增
- **9 个新代理** — 代理系统从 6 扩展到 15
  - `opc-debugger` — 科学方法调试（假设-证据-排除 4 阶段循环）
  - `opc-security-auditor` — OWASP ASVS 安全审计 + 密钥/注入/配置扫描
  - `opc-doc-writer` — 从代码自动生成技术文档
  - `opc-doc-verifier` — 文档准确性验证（覆盖率+新鲜度+链接）
  - `opc-codebase-mapper` — 4 维代码地图（技术栈/架构/质量/关注点）
  - `opc-ui-auditor` — 6 支柱 UI 审计（文案/视觉/颜色/排版/间距/体验）
  - `opc-plan-checker` — 8 维度计划验证（Pre-flight Gate）
  - `opc-assumptions-analyzer` — 隐藏假设分析（技术/用户/商业/运维）
  - `opc-roadmapper` — 产品路线图生成（ICE 评分 + 北极星导航）
- **波次执行引擎** — `skills/engineering/parallel-agents/SKILL.md`
  - DAG 依赖分析 → 波次分组 → 并行派发
  - 波前验证（波次 N+1 验证 N 产物）
  - 失败隔离 + 最多 2 次重试
- **STATE.md 文件锁提示** — `scripts/hooks/state_file_lock.py`
  - 基于文件锁标记的建议性守卫（30s 超时判定，后续写入时清理旧锁）
  - 用于提示并行波次执行中的潜在写入冲突，不提供严格阻塞式锁语义

### 变更
- 更新 `AGENTS.md` 添加 5 条新协作流水线（调试/安全/文档/规划验证）
- 更新 `README.md` 架构图（15 代理 + parallel-agents 技能）
- 更新 `ROADMAP.md` 标记 v0.3.0 完成
- 更新 `hooks/hooks.json` 注册 state-file-lock 钩子

---

## [0.2.0] - 完成

### 新增
- **Hooks 系统** — `hooks/hooks.json` 钩子注册表 + 11 个钩子脚本
  - `block-no-verify` — 阻止 git --no-verify 绕过
  - `commit-quality` — Conventional Commits 格式 + 密钥检测
  - `read-before-edit` — 先读后改提醒
  - `config-protection` — linter 配置保护
  - `prompt-injection-scan` — 提示注入模式检测
  - `command-audit-log` — 命令审计日志
  - `console-log-warn` — debug 语句提醒
  - `git-push-reminder` — 推送前检查清单
  - `session-summary` — 会话活动持久化
  - `statusline` — 模型+任务+目录+上下文使用率进度条
  - `state-file-lock` — STATE.md 并行写入防护
- **Rules 系统** — 编码规则目录（4 语言 17 文件）
  - `rules/common/` — 5 个通用规则（coding-style, security, testing, git-workflow, patterns）
  - `rules/typescript/` — 3 个 TypeScript 规则（coding-style, testing, security）
  - `rules/csharp/` — 3 个 C# 规则（coding-style, testing, security）
  - `rules/python/` — 3 个 Python 规则（coding-style, testing, security）
  - `rules/kotlin/` — 3 个 Kotlin/Android 规则（coding-style, testing, security）
- **References 系统** — 引用文档目录
  - `references/gates.md` — 4 种门控分类
  - `references/verification-patterns.md` — 验证模式（存在→实质→接线→功能）
  - `references/anti-patterns.md` — 通用反模式
  - `references/context-budget.md` — 上下文预算规则
  - `references/tdd.md` — TDD 参考
  - `references/git-integration.md` — Git 集成参考
- **多工具格式转换** — `scripts/convert.py`
  - 支持 Cursor (.mdc)、Windsurf (.windsurfrules)、Gemini CLI、OpenCode、OpenClaw
  - 一键转换 37 个技能/代理/命令到 5 种工具格式
- **文档**
  - `CONTRIBUTING.md` — 完整贡献指南（技能/代理/命令/钩子贡献规范）
  - `SECURITY.md` — 安全策略
  - `CHANGELOG.md` — 变更日志

### 变更
- 更新 `CLAUDE.md` 项目结构添加 hooks/ 和 scripts/
- 更新 `README.md` 添加钩子系统文档和多工具安装指南
- 更新 `.claude-plugin/plugin.json` 注册 hooks
- 更新 `.gitignore` 排除 integrations/ 和 .opc/ 运行时文件
- 更新 `ROADMAP.md` 标记 v0.2.0 已完成项目

---

## [0.1.0] - 2025-XX-XX

### 新增
- **技能系统** — 24 个技能
  - `skills/using-superopc/` — 元技能
  - `skills/product/` — 产品技能组（brainstorming, planning, implementing, reviewing, shipping）
  - `skills/engineering/` — 工程技能组（tdd, debugging, git-worktrees）
  - `skills/business/` — 商业技能组（10 个极简创业技能）
  - `skills/intelligence/` — 情报技能组（market-research, follow-builders）
  - `skills/learning/` — 学习技能组（skill-from-masters, writing-skills, continuous-learning）
- **代理系统** — 6 个核心代理
  - `opc-orchestrator` — 全流程编排器
  - `opc-planner` — 规划专家
  - `opc-executor` — 执行专家
  - `opc-reviewer` — 审查专家
  - `opc-researcher` — 研究专家
  - `opc-verifier` — 验证专家
- **命令系统** — 7 个 `/opc-*` 命令
- **系统指令** — `CLAUDE.md` + `AGENTS.md`
- **插件清单** — `.claude-plugin/plugin.json` + `marketplace.json`
- **路线图** — `ROADMAP.md`（v0.1.0 到 v2.0.0，480 行）
- **许可证** — MIT
