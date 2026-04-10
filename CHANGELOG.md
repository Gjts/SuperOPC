# Changelog

所有 SuperOPC 的显著变更记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [0.3.0] - 进行中

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

### 变更
- 更新 `AGENTS.md` 添加 5 条新协作流水线（调试/安全/文档/规划验证）
- 更新 `README.md` 架构图（15 代理 + parallel-agents 技能）
- 更新 `ROADMAP.md` 标记 v0.3.0 完成项

---

## [0.2.0] - 完成

### 新增
- **Hooks 系统** — `hooks/hooks.json` 钩子注册表 + 9 个钩子脚本
  - `block-no-verify` — 阻止 git --no-verify 绕过
  - `commit-quality` — Conventional Commits 格式 + 密钥检测
  - `read-before-edit` — 先读后改提醒
  - `config-protection` — linter 配置保护
  - `prompt-injection-scan` — 提示注入模式检测
  - `command-audit-log` — 命令审计日志
  - `console-log-warn` — debug 语句提醒
  - `git-push-reminder` — 推送前检查清单
  - `session-summary` — 会话活动持久化
- **Rules 系统** — 编码规则目录
  - `rules/common/` — 5 个通用规则（coding-style, security, testing, git-workflow, patterns）
  - `rules/typescript/` — 3 个 TypeScript 规则（coding-style, testing, security）
  - `rules/csharp/` — 3 个 C# 规则（coding-style, testing, security）
- **References 系统** — 引用文档目录
  - `references/gates.md` — 4 种门控分类
  - `references/verification-patterns.md` — 验证模式（存在→实质→接线→功能）
  - `references/anti-patterns.md` — 通用反模式
  - `references/context-budget.md` — 上下文预算规则
  - `references/tdd.md` — TDD 参考
  - `references/git-integration.md` — Git 集成参考
- **多工具格式转换** — `scripts/convert.js`
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
