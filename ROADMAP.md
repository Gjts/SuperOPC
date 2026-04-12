# SuperOPC Roadmap — v0.1.0 to v2.0.0

> 融合 GSD(103+功能/69命令/24代理) + ECC(181技能/hooks/rules) + Superpowers + Agency-Agents(192代理/15类别) + 6个其他项目

---

## 阶段一：基础系统 (v0.1 - v0.5)

### v0.1.0 [已完成] — 骨架搭建

24技能 + 6代理 + 7命令 + 插件清单 + 系统指令 + README

---

### v0.2.0 [已完成] — Hooks + Rules + 引用系统

**目标：** 自动化质量门控 + 多语言编码规则 + 共享知识库

#### Hooks 系统（融合 ECC hooks.json + GSD 9个钩子）
- [x] `hooks/hooks.json` — 统一钩子注册表（10个钩子，9个脚本）
- [x] **PreEdit Hook**: read-before-edit 守卫（GSD gsd-read-guard）
- [x] **PreCommit Hook**: 提交质量检查 commit格式+密钥扫描（ECC+GSD）
- [x] **PostToolUse Hook**: 命令审计日志 + console.log 警告 + git push 提醒
- [x] **PreWrite Hook**: 提示注入检测 + 配置保护 + 文档路径警告
- [x] **StatusLine Hook**: 模型+任务+目录+上下文使用率（GSD statusline）

#### Rules 系统（融合 ECC rules/ 12语言）
- [x] `rules/common/` — coding-style, security, testing, git-workflow, patterns（5文件）
- [x] `rules/typescript/` — Next.js 14（coding-style, testing, security）
- [x] `rules/csharp/` — .NET 8（coding-style, testing, security）
- [x] `rules/python/` + `rules/kotlin/` — Python 3.11+ / Android Kotlin
- [ ] 按需扩展：golang, rust, java, swift, dart, php

#### References 引用系统（融合 GSD 35个引用文档）
- [x] `references/gates.md` — 4种门控（Pre-flight/Revision/Escalation/Abort）
- [x] `references/verification-patterns.md` — 验证模式（存在→实质→接线→功能）
- [x] `references/anti-patterns.md` — 通用反模式（24条规则）
- [x] `references/context-budget.md` — 上下文预算（4层级退化）
- [x] `references/tdd.md` + `references/git-integration.md`

#### 文档补全
- [x] CONTRIBUTING.md + SECURITY.md
- [x] CHANGELOG.md
- [x] `scripts/convert.py` — 多工具格式转换（Cursor/Windsurf/Gemini/OpenCode/OpenClaw）

---

### v0.3.0 [已完成] — 代理扩展 + 波次执行

**目标：** 6到15代理 + 并行波次执行引擎

#### 新增代理（融合 GSD 24代理 + ECC）
- [x] **opc-debugger** — 持久化调试（假设-证据-排除-修复，科学方法4阶段循环）
- [x] **opc-security-auditor** — 威胁模型安全审计（OWASP ASVS + 密钥/注入/配置扫描）
- [x] **opc-doc-writer** + **opc-doc-verifier** — 文档生成+准确性验证
- [x] **opc-codebase-mapper** — 4维代码地图（技术栈/架构/质量/关注点）
- [x] **opc-ui-auditor** — 6支柱UI审计（文案/视觉/颜色/排版/间距/体验）
- [x] **opc-plan-checker** — 8维度计划验证循环（Pre-flight Gate）
- [x] **opc-assumptions-analyzer** — 代码优先假设分析（技术/用户/商业/运维）
- [x] **opc-roadmapper** — 路线图生成（ICE评分 + 北极星导航）

#### 波次执行引擎（融合 GSD + Superpowers）
- [x] 依赖分析 - 波次分组 - 并行派发
- [x] STATE.md 文件锁（防并行写入冲突）
- [x] 波前依赖检查（波次N+1验证N产物）
- [x] 技能 `skills/engineering/parallel-agents/SKILL.md`


### v0.4.0 [已完成] — 状态管理 + 文件系统

**目标：** 引入 .opc/ 文件级状态管理——可读、可追踪、可 git

#### .opc/ 状态目录（融合 GSD .planning/）

```
.opc/
  PROJECT.md            # 项目愿景、约束、决策
  REQUIREMENTS.md       # 需求：v1/v2/超范围
  ROADMAP.md            # 阶段路线图+状态追踪
  STATE.md              # 活状态：位置、决策、阻塞、指标
  config.json           # 工作流配置
  phases/               # 阶段目录
    XX-phase-name/
      XX-CONTEXT.md     # 用户偏好（讨论阶段）
      XX-RESEARCH.md    # 生态研究
      XX-YY-PLAN.md     # 执行计划
      XX-YY-SUMMARY.md  # 执行结果
      XX-VERIFICATION.md
  research/             # 项目级研究
  debug/                # 调试会话+知识库
  quick/                # 快速任务追踪
  todos/                # 待办项
  threads/              # 持久上下文线程
  seeds/                # 前瞻性想法种子
```

#### 配置系统（融合 GSD config.json 30+设置项）
- [x] 工作流开关：research, plan_check, verifier, nyquist, node_repair, code_review
- [x] 模型配置：quality / balanced / budget / inherit / adaptive
- [x] 粒度控制：coarse(3-5) / standard(5-8) / fine(8-12)
- [x] Git 策略：none / phase / milestone

#### 模板系统（融合 GSD templates/）
- [x] project.md, requirements.md, roadmap.md, state.md 模板
- [x] phase-prompt.md, summary.md, debug.md 模板

---

### v0.5.0 [已完成] — 工程技能深化

**目标：** 3到16工程技能，覆盖全栈+技术栈专属

#### 通用工程技能（融合 ECC skills/）
- [x] `api-design/` — RESTful + GraphQL
- [x] `database-migrations/` — 迁移 + ORM schema drift 检测
- [x] `docker-patterns/` — 容器化模式
- [x] `deployment-patterns/` — 蓝绿/金丝雀/滚动
- [x] `security-review/` — OWASP Top 10
- [x] `e2e-testing/` — Playwright
- [x] `architecture-decision-records/` — ADR
- [x] `frontend-patterns/` + `backend-patterns/`
- [x] `verification-loop/` — Nyquist + 节点修复
- [x] `codebase-onboarding/` — 棕地映射
- [x] `code-review-pipeline/` — quick/standard/deep 三级

#### 技术栈专属
- [x] `nextjs-patterns/` — Next.js 14 App Router
- [x] `dotnet-patterns/` — .NET 8 Minimal API + EF Core
- [x] `postgres-patterns/` — PostgreSQL 15
- [x] `kotlin-compose/` — Jetpack Compose

---

## 阶段二：能力深化 (v0.6 - v1.0)

### v0.6.0 [已完成] — 商业技能深化 + 仪表盘

**目标：** 10到18商业技能 + OPC仪表盘

#### 新增技能
- [x] `legal-basics/` — 商标、合同、隐私政策、GDPR 风险盘点
- [x] `finance-ops/` — 记账、税务、发票、MRR / Burn / Runway
- [x] `investor-materials/` — 投资材料（deck / memo / data room）
- [x] `product-lens/` — 产品视角审查（激活 / 留存 / PMF 信号）
- [x] `seo/` — SEO优化（意图词 + 内容集群 + money pages）
- [x] `content-engine/` — 内容引擎（输入→生产→分发→复用）
- [x] `brand-voice/` — 品牌语调（支柱 + 禁用词 + 场景映射）
- [x] `user-interview/` — The Mom Test 方法论

#### 仪表盘（融合 GSD stats + manager）
- [x] `/opc-dashboard` — 项目全貌：进度+MRR+债务+下一步
- [x] `/opc-stats` — 项目指标：阶段/计划/需求/git

---

### v0.7.0 [已完成] — 多工具适配 + MCP

**目标：** 支持 10+ AI 编码运行时，并提供可复制的 MCP 模板

#### MCP 服务器配置（融合 ECC mcp-configs/）
- [x] Context7 + Supabase + Sequential Thinking + Playwright MCP
- [x] `mcp-configs/mcp-servers.json` 作为运行时 MCP 条目复制源
- [x] `.mcp.json` 最小默认示例

#### 多运行时适配（融合 GSD 运行时模式）
- [x] Claude Code / Cursor / Windsurf / Copilot / Gemini CLI
- [x] OpenCode / Codex / Trae / Cline / Augment Code / OpenClaw
- [x] `scripts/convert.py` — Python 格式转换脚本
- [x] 运行时自动检测 + 钩子事件映射 + 工具名映射

---

### v0.8.0 — 会话管理 + 高级工作流

**目标：** 跨会话持续性 + 自主/快速/讨论模式

#### 会话管理（融合 GSD pause/resume/progress）
- [x] `/opc-pause` — 保存位置到 HANDOFF.json
- [x] `/opc-resume` — 恢复上下文
- [x] `/opc-progress` — 位置+下一步+完成度+验证欠债
- [x] `/opc-session-report` — 会话报告

#### 高级工作流（融合 GSD 自主/快速/讨论）
- [x] `/opc-autonomous [--from N] [--to N] [--only N] [--interactive]`
- [x] `/opc-fast` — 微任务行内执行
- [x] `/opc-discuss` — 纯讨论不执行
- [x] `/opc-explore` — 苏格拉底式探索
- [x] `/opc-do` — 自然语言意图路由
- [x] `/opc-next` — 自动检测并推进下一步

#### 上下文线程（融合 GSD threads + seeds + backlog）
- [x] `/opc-thread` + `/opc-seed` + `/opc-backlog`


### v0.9.0 — 质量保证体系

**目标：** SuperOPC自身 + 用户项目的全面质量体系

#### 技能压力测试
- [x] 每个技能编写压力场景
- [x] 无技能偏差 vs 有技能纠正验证
- [x] 回归测试

#### QA功能群（融合 GSD）
- [x] Nyquist 验证 — 需求到测试覆盖映射
- [x] 节点修复 — RETRY / DECOMPOSE / PRUNE
- [x] `/opc-health [--repair]` — 目录完整性检查
- [x] 跨阶段回归门 — 前序阶段测试套件
- [x] 需求覆盖门 — 计划必须覆盖所有需求
- [x] Schema drift 检测 — ORM修改必须有迁移
- [x] 范围缩减检测 — 三层防御
- [x] 声明溯源标记 — 研究结论标注来源

#### CI/CD
- [x] GitHub Actions: lint + 链接检查 + frontmatter校验 + 注入扫描
- [x] 版本发布自动化

---

### v1.0.0 [已完成] — 正式发布

**目标：** 开源社区就绪的稳定版本

#### 质量标准
- [x] 所有技能通过压力测试
- [x] 完整双语文档（中+英）
- [x] CI/CD 全绿
- [x] 4 项目模板 + 3 使用示例
- [x] 11 AI工具适配

#### 项目模板
- [x] `templates/projects/saas-starter/` — Next.js + Supabase + Stripe
- [x] `templates/projects/api-service/` — .NET 8 + PostgreSQL
- [x] `templates/projects/mobile-app/` — Kotlin + Compose
- [x] `templates/projects/landing-page/` — Next.js 静态导出

#### 社区建设
- [x] GitHub Discussions + Issue/PR 模板 + Discord/微信规划
- [x] Product Hunt 发布准备
- [x] Building in Public 教程（`docs/building-in-public.md`）
- [x] 贡献者奖励机制（`docs/contributor-rewards.md`）

---

## 阶段三：智能进化 (v1.1 - v1.5)

### v1.1.0 — 开发者画像 + 全局学习

**目标：** AI从每次交互中学习，个性化适应开发者

#### 开发者画像（融合 GSD 8维度 profiling）
- [x] `/opc-profile [--questionnaire] [--refresh]`
- [x] 8维度：沟通风格、决策模式、调试方式、UX偏好、技术选择、摩擦触发、学习风格、解释深度
- [x] 生成 USER-PROFILE.md + CLAUDE.md 配置段
- [x] 6问快速问卷系统 + 行为推断引擎
- [x] `skills/using-superopc/developer-profile/SKILL.md` — 画像技能文档

#### 全局学习存储（融合 GSD 功能89 + ECC Continuous Learning v2）
- [x] 跨会话跨项目学习持久化
- [x] 阶段完成时自动复制洞察到全局存储
- [x] 计划器启动时注入相关历史学习
- [x] 观察管道：PostToolUse 钩子 → JSONL → 模式检测 → 本能演化
- [x] `scripts/hooks/observe.py` — 工具使用观察钩子
- [x] `learning_store.detect_patterns()` + `evolve_instincts()` + `prune_observations()`

#### 子代理双阶段审查（融合 Superpowers subagent-driven-development）
- [x] `skills/engineering/subagent-driven-development/SKILL.md` — 主技能
- [x] 实现者 / 规格审查 / 代码质量审查三个子代理提示模板
- [x] AGENTS.md 子代理驱动开发流水线
- [x] parallel-agents 交叉引用

#### 可查询代码库智能（融合 GSD 功能90）
- [x] `/opc-intel [query|status|diff|refresh]`
- [x] .opc/intel/ JSON索引：stack, api-map, dependency-graph, file-roles, arch-decisions
- [x] `scripts/engine/intel_engine.py` — 核心引擎（query/status/diff/write/snapshot/validate）
- [x] `agents/opc-intel-updater.md` — 代码库分析代理（7步探索流程 + 输出预算 + 上下文分级）

---

### v1.2.0 — CLI 工具层

**目标：** SuperOPC CLI — 代理和工作流的程序化基础

#### opc-tools CLI（融合 GSD gsd-tools.cjs 19模块）
- [ ] `bin/opc-tools.cjs` — 核心CLI
- [ ] 域模块：state, phase, roadmap, config, verify, template, init, security, model-profiles, workstream
- [ ] `--raw` 机器可读输出 + `--cwd` 沙箱操作
- [ ] Windows 路径规范化

---

### v1.3.0 — 安全强化

**目标：** 纵深防御——提示注入到路径遍历

#### 安全系统（融合 GSD 功能46/60/99）
- [ ] 集中安全模块：路径遍历防护、注入检测、安全JSON、字段验证、Shell净化
- [ ] 增强注入检测：Unicode不可见字符、编码混淆、熵分析
- [ ] `/opc-secure [N]` — OWASP ASVS 1-3级威胁模型验证
- [ ] 所有安全措施为建议性，不阻止合法操作

---

### v1.4.0 — 领域代理库

**目标：** 融合 Agency-Agents 192代理，按一人公司需求精选

#### 工程代理（精选自 engineering/ 26个）
- [ ] backend-architect, frontend-developer, mobile-app-builder
- [ ] devops-automator, security-engineer, database-optimizer
- [ ] ai-engineer, rapid-prototyper, technical-writer

#### 营销代理（精选自 marketing/ 29个）
- [ ] seo-specialist, content-creator, growth-hacker
- [ ] social-media-strategist, podcast-strategist
- [ ] linkedin-content-creator, twitter-engager, reddit-community-builder

#### 策略+其他代理
- [ ] strategy-nexus（战略协调）, strategy-playbooks（战术手册）
- [ ] product-manager, design-brand-guardian, sales-closer
- [ ] support-agent, testing-qa-engineer

#### 代理路由器
- [ ] 用户意图自动匹配最佳领域代理
- [ ] 领域代理与核心代理(opc-*)协作协议


### v1.5.0 — 高级调试 + 取证

**目标：** 系统化调试、事后分析、安全撤销

#### 调试系统（融合 GSD 功能28/76）
- [ ] `/opc-debug [desc] [--diagnose]`
- [ ] 持久调试会话 + 假设追踪 + knowledge-base.md
- [ ] `--diagnose` 仅诊断不修复

#### 取证（融合 GSD 功能49）
- [ ] `/opc-forensics` — Git历史异常+工件完整性+只读报告

#### 安全撤销（融合 GSD 功能95）
- [ ] `/opc-undo [--last N | --phase NN | --plan NN-MM]`
- [ ] 依赖检查 + 硬确认门

#### 跨AI同行评审（融合 GSD 功能42）
- [ ] `/opc-peer-review --phase N [--gemini] [--claude] [--codex] [--all]`
- [ ] 生成 REVIEWS.md 供计划阶段消费

---

## 阶段四：平台化 (v1.6 - v2.0)

### v1.6.0 — 工作流引擎

**目标：** 命令驱动升级到工作流引擎驱动

#### 工作流定义（融合 GSD 68个工作流）
- [ ] `workflows/` 目录——编排逻辑与命令分离
- [ ] 五大工作流类型：初始化、阶段执行、快速任务、调试、研究
- [ ] 薄编排器：加载上下文、派发代理、收集结果、更新状态
- [ ] 每代理全新200K上下文窗口（1M模型自适应）

#### 自适应上下文（融合 GSD Adaptive Context Enrichment）
- [ ] 500K+窗口自动注入更多上下文
- [ ] 200K窗口截断+缓存友好排序
- [ ] Markdown感知截断（保留标题/需求/任务）

---

### v1.7.0 — 国际化

**目标：** 全球化就绪

#### 文档国际化（融合 GSD 功能57）
- [ ] 中/英/日/韩/葡 五语言文档
- [ ] 翻译同步机制

#### 响应语言配置（融合 GSD 功能83）
- [ ] `response_language` 跨阶段语言一致
- [ ] 中国市场特化代理（Agency-Agents）：
  - 微信小程序、百度SEO、小红书、抖音、B站
  - 快手、微博、知乎、跨境电商、直播带货

---

### v1.8.0 — 企业级功能

**目标：** 多项目、多工作流、团队协作

#### 工作流命名空间（融合 GSD 功能51）
- [ ] `/opc-workstreams` — 并行工作流隔离

#### 管理者仪表盘（融合 GSD 功能52）
- [ ] `/opc-manager` — 多阶段交互式命令中心

#### 里程碑管理（融合 GSD 功能8/50）
- [ ] `/opc-audit-milestone` + `/opc-complete-milestone` + `/opc-new-milestone`
- [ ] `/opc-milestone-summary` — 团队入职摘要
- [ ] 间隙关闭 — 缺口自动创建修复阶段

#### 多仓库 + 项目前缀（融合 GSD 功能47/67）
- [ ] 多仓库自动检测 + 跨仓库提交哈希
- [ ] `project_code: "ABC"` 阶段目录前缀

---

### v1.9.0 — SDK + 可编程接口

**目标：** SuperOPC可编程化

#### SDK（融合 GSD SDK 功能58）
- [ ] TypeScript SDK — 无头运行工作流
- [ ] npm 包 `superopc`
- [ ] API: init / plan / build / ship

#### 安装器（融合 GSD installer）
- [ ] `npx superopc` — 交互式安装（10+运行时）
- [ ] 全局/本地 + 清洁卸载 + 补丁备份

---

### v2.0.0 — 超级一人公司操作系统

**目标：** 功能完备、社区繁荣、生态成熟

#### 功能完备度
- [ ] 60+ 技能覆盖全领域
- [ ] 30+ 代理（核心+领域）覆盖全职能
- [ ] 20+ 命令覆盖完整生命周期
- [ ] 10+ AI工具适配
- [ ] CLI + SDK + npm包

#### 质量标准
- [ ] 全技能压力测试通过
- [ ] 5语言文档 + CI/CD全绿
- [ ] 5+ 模板 + 10+ 示例
- [ ] 安全审计通过

#### 生态系统
- [ ] Plugin Marketplace（OpenClaw + Claude Code）
- [ ] 社区钩子生态 + 第三方技能协议
- [ ] 技能市场/注册表 + 社区模板库

---

## 版本总览

| 阶段 | 版本 | 核心主题 | 复杂度 | 新增文件 | 来源融合 |
|------|------|---------|--------|---------|---------|
| 基础 | v0.1.0 | 骨架搭建 | - | 41 | - |
| | v0.2.0 | Hooks+Rules+引用 | 高 | ~25 | ECC hooks+GSD hooks+ECC rules |
| | v0.3.0 | 代理扩展+波次 | 高 | ~15 | GSD 24代理+Superpowers |
| | v0.4.0 | 状态管理+文件 | 高 | ~20 | GSD .planning/+config |
| | v0.5.0 | 工程技能深化 | 中 | ~17 | ECC skills+GSD功能 |
| 深化 | v0.6.0 | 商业技能+仪表盘 | 中 | ~12 | ECC+Agency-Agents |
| | v0.7.0 | 多运行时+MCP | 高 | ~15 | GSD 运行时模式+ECC MCP |
| | v0.8.0 | 会话+高级工作流 | 高 | ~18 | GSD 会话/自主/线程 |
| | v0.9.0 | 质量保证 | 高 | ~15 | GSD QA功能群 |
| | v1.0.0 | 正式发布 | 中 | ~20 | 模板+示例+社区 |
| 智能 | v1.1.0 | 画像+学习 | 高 | ~12 | GSD profiling+learnings |
| | v1.2.0 | CLI工具层 | 高 | ~15 | GSD gsd-tools 19模块 |
| | v1.3.0 | 安全强化 | 中 | ~8 | GSD security+OWASP |
| | v1.4.0 | 领域代理库 | 高 | ~25 | Agency-Agents 192精选 |
| | v1.5.0 | 调试+取证 | 中 | ~10 | GSD debug/forensics/undo |
| 平台 | v1.6.0 | 工作流引擎 | 高 | ~20 | GSD 68工作流 |
| | v1.7.0 | 国际化 | 中 | ~30 | GSD i18n+Agency中国市场 |
| | v1.8.0 | 企业级 | 高 | ~15 | GSD workstream/manager |
| | v1.9.0 | SDK+API | 高 | ~20 | GSD SDK+installer |
| | v2.0.0 | 超级OPC OS | 中 | ~15 | 全面融合+生态 |

**总计：** ~350+ 文件，融合 7 个来源项目

---

## 优先级原则

1. **用户价值优先** — 每个版本让使用者立即感受到改进
2. **小步快跑** — 每版本聚焦一个主题
3. **吃自己的狗粮** — 用SuperOPC开发SuperOPC
4. **社区驱动** — 开源后根据反馈调优先级
5. **深度融合** — 重新设计融合，保持一人公司视角一致性
6. **安全第一** — 建议性优于强制性

---

## 来源项目融合索引

| 来源 | 贡献 | 融合版本 |
|------|------|---------|
| **GSD** | 103+功能, 69命令, 68工作流, 24代理, 35引用, 19 CLI模块, 9钩子 | v0.2-v1.9 |
| **ECC** | 181技能, hooks.json, rules/(12语言), MCP, scripts | v0.2/v0.4/v0.5/v0.6/v0.7 |
| **Superpowers** | 并行代理调度, 完成验证, 技能优先规则 | v0.1/v0.3 |
| **Agency-Agents** | 192代理/15类别 | v1.4/v1.7 |
| **Minimalist Entrepreneur** | 10个商业技能 | v0.1 |
| **Follow Builders** | 构建者追踪情报 | v0.1 |
| **Skill From Masters** | 案例驱动技能创建 | v0.1 |
| **last30days** | 30天技能系统 | v0.1 |
