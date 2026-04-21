# Changelog

所有 SuperOPC 的显著变更记录在此文件。

格式基于 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.0.0/)，
版本号遵循 [Semantic Versioning](https://semver.org/lang/zh-CN/)。

---

## [1.4.1] - Skill-Driven Runtime (Phase A)

**主题：** 把 skill 发现机制从"LLM 自由匹配 17 份 SKILL.md description"升级为
"Registry + 三级路由 L1 命中 / L3 兜底"的可审计结构化管道。Context 成本降至原 30%
以下，保持 v1.4 skill-dispatcher / agent-workflow 契约完全向后兼容。详见
`docs/SKILL-DRIVEN-DESIGN.md` §5.1 与 `docs/plans/2026-04-21-skill-driven-runtime-phase-a.md`。

### 架构

- **Skill Registry（生成式）**：从 17 份 SKILL.md frontmatter 聚合生成
  `skills/registry.json`，作为三级路由的单一事实源。`skills/registry.schema.json`
  定义 JSON Draft-07 契约。
- **Intent Router 三级**：L1 关键词/短语打分（阈值 20）→ L2 Embedding（Phase A 跳过）
  → L3 LLM fallback（Phase A 使用 mock）。全级 miss 回落到 `using-superopc`。
- **审计日志**：每次 `IntentRouter.route()` 调用写 `.opc/routing/<today>.jsonl`
  （含 input_hash，不落原文）。`observe.py` 同步到 `~/.opc/learnings/skill_routing.jsonl`。

### 新增

- **`skills/registry.schema.json`** — 17 行 field 白名单 + type enum + semver 正则
- **`skills/registry.json`** — 生成产物：8 dispatcher + 4 atomic + 4 meta + 1 learning
- **`scripts/build_skill_registry.py`** — frontmatter → registry.json 生成器
  * `--check` 模式检测 drift，退出非零
  * `--registry PATH` 自定义校验路径
  * 稳定排序保证可重入，`generated_at` 忽略 diff
- **`scripts/engine/intent_router.py`** — `IntentRouter.route(input)` 结构化路由
  * 返回 `skill_id / confidence / path / latency_ms / candidates_explored`
  * `_call_llm(prompt, candidates)` 模块级 mock，Phase B 替换真实 LLM
  * 发送 `skill.routed` 事件到 event_bus
- **`docs/SKILL-DRIVEN-DESIGN.md`** — 现状诊断 + 四组件 schema + 两条演进路线（A/B）+ 决策清单
- **`docs/adr/0001-skill-registry-schema.md`** — 生成式 Registry 与 frontmatter 扩展决策
- **`docs/adr/0002-intent-router-tiers.md`** — L1/L2/L3 三级递进决策
- **`docs/adr/0003-orchestration-grain.md`** — 编排粒度双绑定（agent 默认 + 可选 skill）
- **`docs/adr/README.md`** — ADR 索引与生命周期
- **`docs/plans/2026-04-21-skill-driven-runtime-phase-a.md`** — 3 波 10 任务 `<opc-plan>` XML，含 Pre-flight Gate 评审记录

### 扩展（不破坏契约）

- **17 份 SKILL.md frontmatter** 新增可选字段 `id / type / tags / dispatches_to / triggers / version`，
  正文零行改动。8 份 dispatcher 显式声明 `dispatches_to` 指向 `agents/registry.json` 中已存在的 agent id。
  `business-advisory.description` 包含冒号已加双引号修复 YAML 歧义
- **`scripts/hooks/observe.py`** 新增 `sync_skill_routing()` 函数，PostToolUse 触发后
  把路由日志的新记录（以 input_hash 去重）拷贝到 `~/.opc/learnings/skill_routing.jsonl`
- **`scripts/opc_quality.py`** 新增 `repo.skill-registry-consistency` 健康检查，
  自动运行 `build_skill_registry.py --check`；drift 时 `opc-health` 报 fail
- **`skills/using-superopc/SKILL.md`** 增补 "v1.4.1 可选加速路径" 段落，
  明示 Registry + Router 是**可选**路径，不替代 skill-first 铁律

### 测试

- **`tests/engine/test_build_skill_registry.py`** — 8 个契约测试（从 RED → GREEN）：
  SKILL.md 数量一致、id 唯一、type 白名单、dispatcher.dispatches_to 存在性、
  registry 通过 JSON Schema、路径存在性、frontmatter/registry 字段一致、`--check` drift 检测
- **`tests/engine/test_intent_router.py`** — 6 个契约测试（从 RED → GREEN）：
  返回结构、L1 命中、L1 miss 直进 L3、三级全 miss 回落、JSONL 日志、`skill.routed` 事件

### 已知限制（预期）

- L2 Embedding 检索延后到 Phase B（`docs/SKILL-DRIVEN-DESIGN.md` §5.2 路线 B）
- L3 使用 mock，真实 LLM 接入在 Phase B
- Context 节省仅对新会话生效，对已开长会话无追溯

### 迁移（无破坏）

- v1.4.0 所有 skill/agent/references 契约 100% 保留
- 老 workflow（直接调用 `Skill` 工具）仍是默认路径
- Registry/Router 为可选加速层，不启用即不影响行为

---

## [1.4.0] - Skill 精简 + Agent 吸收 + references/ 知识层

**主题：** 把 v1.3 的三层契约推到极限。skill 空间只保留"真正驱动 agent workflow"的入口和被 agent 调用的原子技术；柔性知识内容（技术栈 patterns / 商业 playbook / rubric / checklist）全部下沉到 `references/` 供 agent workflow 引用。详见 `docs/plans/2026-04-17-architecture-refactor.md`。

### 架构

- **四层契约**：Command → Dispatcher Skill → Agent → (Atomic Skill | references/)
- **skill 从 30 → 17**（-43%）：只保留驱动型 skill，柔性知识下沉
- **agent 从 17 → 18**：新增 `opc-business-advisor` 作为 20 个商业子活动的统一入口
- **references/ 成为第四层**：13 个技术 patterns + 19 个商业 playbook + 2 个 intelligence 方法论 + 3 个 rubric/checklist/authoring

### 新增

- **`agents/opc-business-advisor.md`** — 一人公司商业顾问 agent，持有 20 个商业子活动的识别 / 路由 / 执行 workflow。Phase 0 子活动识别 + Anti-Build-Trap HARD-GATE + Phase 2 按 `references/business/<sub-activity>.md` 方法论执行或委派 domain agent
- **`skills/business/advisory/SKILL.md`** — 商业活动统一派发器（50 行）
- **`references/business/*.md`** — 19 个一人公司 playbook（从 skills/business/ 迁移）
- **`references/patterns/engineering/*.md`** — 13 个技术栈 patterns（从 skills/engineering/ 迁移）
- **`references/intelligence/*.md`** — market-research / follow-builders（从 skills/intelligence/ 迁移）
- **`references/security-checklist.md`** — OWASP Top 10 完整清单（从旧 security-review SKILL 抽取）
- **`references/review-rubric.md`** 扩展三级审查深度（Quick/Standard/Deep，从旧 code-review-pipeline 抽取）
- **`references/skill-authoring.md`** — skill 作者手册（合并 skill-from-masters + writing-skills）

### 变更（agent 吸收完整 workflow）

- `opc-reviewer.md` — 吸收 Quick/Standard/Deep 三级审查深度（Wave 2.2）
- `opc-security-auditor.md` — 吸收 OWASP Top 10 完整 workflow，引用 `references/security-checklist.md`（Wave 2.3）
- `opc-debugger.md` — 吸收调试修复规程（失败测试先行 / 单一修复 / ≥3 次失败质疑架构，Wave 2.4）
- `opc-business-advisor.md` — 新 agent 持有 20 个商业子活动的完整 workflow（Wave 2.1）

### 变更（skill 瘦身为 dispatcher）

- `skills/engineering/security-review/SKILL.md` — 139 → 35 行
- `skills/engineering/debugging/SKILL.md` — 118 → 37 行
- `skills/product/planning/SKILL.md` — 扩展触发面覆盖旧 brainstorming，添加 HARD-GATE
- `skills/business/advisory/SKILL.md` — 新建 50 行派发器

### 变更（skill 合并）

- **brainstorming 合并入 planning**：两者都派发给 opc-planner，由 agent 根据输入成熟度自动路由到 Phase 0-1 或 Phase 2-5（Wave 3.4b）

### 移除（下沉到 references/）

- `skills/business/` 下 19 个 playbook 目录（pricing / mvp / validate-idea / first-customers / find-community / processize / seo / content-engine / brand-voice / marketing-plan / grow-sustainably / user-interview / investor-materials / legal-basics / finance-ops / company-values / product-lens / daily-standup / minimalist-review）→ `references/business/`
- `skills/engineering/` 下 13 个技术栈 patterns（nextjs / dotnet / postgres / docker / kotlin-compose / api-design / ADR / codebase-onboarding / database-migrations / deployment / e2e-testing / frontend / backend / code-review-pipeline）→ `references/patterns/engineering/`
- `skills/intelligence/` 整个目录 → `references/intelligence/` + `skills/using-superopc/autonomous-ops/`（元层）
- `skills/learning/skill-from-masters/` + `skills/learning/writing-skills/` → `references/skill-authoring.md`
- `skills/product/brainstorming/` → 合并到 `skills/product/planning/`

### 迁移映射

见 `AGENTS.md` 的 "v1.4 迁移" 章节。外部文档引用旧 skill 路径须按表替换为新的 `Skill("business-advisory")` / `references/business/*.md` / `references/patterns/engineering/*.md` 等路径。

### 统计

| 项 | v1.3 | v1.4 | 变化 |
|---|---|---|---|
| Skill 文件 | ~30 | 17 | -43% |
| 其中 dispatcher | 6 | 8 | +2（security-review、business-advisory） |
| 其中 atomic | 4 | 4 | 持平 |
| 其中 meta | 4 | 4 | 持平（autonomous-ops 从 intelligence 迁入 using-superopc） |
| 其中 learning | 3 | 1 | -2（skill-from-masters + writing-skills 合并到 references） |
| 其中 product | 5 | 4 | -1（brainstorming 合并入 planning） |
| Agent 文件 | 17 | 18 | +1（opc-business-advisor） |
| references 知识条目 | ~15 | ~50 | +35（19 business + 13 patterns + 2 intel + 3 rubric/checklist/authoring） |

### 兼容性

- `scripts/convert.py` SKILL_DIRS 移除 `skills/intelligence`，其余自动适配
- `.claude-plugin/plugin.json` version 1.0.0 → **1.4.0**（长期与 CHANGELOG 脱节，顺便修正），agents 列表追加 `opc-business-advisor`
- `scripts/engine/` v2 engine 完全不受影响
- `hooks/` / `rules/` / `commands/` / `agents/registry.json` schema 保持兼容

### 回滚

- 每个 Wave 独立 commit，任一 Wave 失败可单独 `git revert <commit>`
- 重构基线 pre-refactor-v1.3 tag 保留

---

## [1.3.0] - 架构重构：Skill-Dispatcher / Agent-Workflow 模式

重大架构变更。将 `command / skill / agent` 三层职责重叠清理为**单源**结构：
agent 独占 workflow，skill 分为两类（dispatcher 触发器 + atomic 原子技术），
command 退化为薄入口。详见 `docs/REFACTOR-PLAN.md` 和 `docs/plans/2026-04-17-architecture-refactor.md`。

### 架构

- **三层契约**：Command (≤ 15 行) → Dispatcher Skill (≤ 30 行) → Agent (workflow 所有者) → Atomic Skill (按需调用)
- **两种 skill**：dispatcher（6 个，派发 agent）/ atomic（～51 个，可复用技术）
- **触发链路**：slash 命令和自然语言走**同一条** skill → agent 链路，零分叉

### 新增

- `references/plan-template.md` — PLAN.md 的 XML+Markdown 标准模板与字段语义
- `references/review-rubric.md` — 五维度代码审查评分表（被 opc-reviewer 引用）
- `agents/opc-shipper.md` — 新 agent，持有完整发布流程（测试验证 / 一人公司检查清单 / 4 选项 / worktree 清理）
- `skills/engineering/agent-dispatch/` — 合并 `parallel-agents` + `subagent-driven-development`，统一 Mode A（串行+双阶段审查）和 Mode B（波次并行）
- `commands/opc/opc.md` — 统一自然语言入口，派发 `workflow-modes` dispatcher

### 变更（瘦身为 dispatcher skill）

- `skills/product/brainstorming/SKILL.md` — 77 → 28 行
- `skills/product/planning/SKILL.md` — 84 → 33 行
- `skills/product/implementing/SKILL.md` — 109 → 31 行
- `skills/product/reviewing/SKILL.md` — 81 → 26 行
- `skills/product/shipping/SKILL.md` — 96 → 30 行
- `skills/using-superopc/workflow-modes/SKILL.md` — 66 → 31 行

### 变更（agent 吸收完整 workflow）

- `agents/opc-planner.md` — 吸收 brainstorming 需求澄清 + 方案比较 + pre-flight gate，现为 Phase 0-5 完整流程
- `agents/opc-executor.md` — 吸收子代理派发 + 双阶段审查 + TDD + 原子提交 + SUMMARY.md
- `agents/opc-reviewer.md` — 引用 `references/review-rubric.md`，补齐一人公司可维护性 6 项检查
- `agents/opc-orchestrator.md` — 双职责：7 模式路由决策树（吸收自 workflow-modes skill） + 流水线编排

### 变更（command 瘦身）

- `commands/opc/plan.md` — 55 → 15 行（仅派发 planning skill）
- `commands/opc/build.md` — 41 → 15 行（仅派发 implementing skill）
- `commands/opc/review.md` — 25 → 12 行（仅派发 reviewing skill）
- `commands/opc/ship.md` — 19 → 14 行（仅派发 shipping skill）

### 移除

- 6 个路由命令合并为单一 `/opc`：
  - `commands/opc/do.md`、`commands/opc/next.md`、`commands/opc/discuss.md`、`commands/opc/explore.md`、`commands/opc/fast.md`、`commands/opc/quick.md`
- 2 个重复 atomic skill 合并为 `agent-dispatch`：
  - `skills/engineering/parallel-agents/`
  - `skills/engineering/subagent-driven-development/`（3 个 prompt 模板 git rename 到新目录）

### 迁移映射（外部引用更新指南）

| 旧路径 | 新路径 |
|---|---|
| `Skill("parallel-agents")` | `Skill("agent-dispatch")` Mode B |
| `Skill("subagent-driven-development")` | `Skill("agent-dispatch")` Mode A |
| `/opc-do` / `/opc-next` / `/opc-discuss` / `/opc-explore` / `/opc-fast` / `/opc-quick` | `/opc` + 自然语言（orchestrator 自动识别模式）|
| `skills/product/*` 中查找 workflow 步骤 | 对应 agent 文件（`opc-planner` / `opc-executor` / `opc-reviewer` / `opc-shipper`）|
| `agents/opc-planner.md` 内找 PLAN.md 模板 | `references/plan-template.md` |
| `skills/product/reviewing/SKILL.md` 内找评分表 | `references/review-rubric.md` |

### 统计

| 项 | v1.2 | v1.3 | 变化 |
|---|---|---|---|
| Skill 文件 | 58 | 57 | -1 |
| 其中 dispatcher skill | 0 | 6 | 新类型 |
| Command 文件 | 27 | 22 | -5 |
| Agent 文件 | 16 | 17 | +1（opc-shipper） |

### 兼容性

- `scripts/convert.py` 导出到 Cursor/Windsurf/Gemini/OpenCode/OpenClaw 自动跟随新结构，无需适配
- `scripts/engine/` v2 engine 完全不受影响（只操作 `agents/registry.json` 和状态层）
- `hooks/`、`rules/`、`references/` 现有文件不变
- `agents/registry.json` schema 保持兼容，仅新增 `opc-shipper` 条目

### 回滚

- 重构基线：git tag `pre-refactor-v1.3`
- 每个 Phase 独立 commit：Phase A（planning 链路样板）/ Phase B（4 链路复制）/ Phase C（atomic skill + command 收敛）/ Phase D（全局扫尾）
- 任一 Phase 失败可单独 `git revert <commit>`

---

## [1.2.0] - CLI 工具层：opc-tools 程序化基础

### 新增
- **opc-tools CLI 入口点** — `bin/opc-tools`
  - Python 实现，直接复用现有 `scripts/engine/` 引擎层
  - 全局标志：`--raw`（机器可读 JSON）、`--cwd`（沙箱操作）、`--pick`（字段提取）
  - `help` 命令输出完整命令文档
- **CLI 核心基础设施** — `scripts/cli/core.py`
  - `output()` / `error()` — 统一输出格式化（JSON 或人类可读）
  - `find_opc_dir()` / `opc_root()` / `opc_paths()` — .opc/ 目录定位和标准路径
  - `load_config()` — 配置加载（默认值 + 用户覆盖 + 嵌套合并）
  - `exec_git()` — Git 命令封装
  - `extract_field()` / `safe_read()` — Markdown 字段提取
  - `normalize_phase_name()` / `generate_slug()` / `find_phase_dir()` — 阶段助手
  - Windows 路径规范化（pathlib 统一）
- **CLI 主路由器** — `scripts/cli/router.py`
  - 10 个顶级命令域路由 + 4 个内联工具命令
  - `consume_cwd()` — 支持 `--cwd=<path>` 和 `--cwd <path>` 两种形式
  - 懒加载域模块以保持启动速度
- **状态域模块** — `scripts/cli/state.py`
  - 12 个子命令：load / get / update / patch / json / begin-phase / advance-plan / record-metric / add-decision / add-blocker / resolve-blocker / record-session
  - `cmd_list_todos()` — 待办事项枚举（支持 area 过滤）
- **配置域模块** — `scripts/cli/config.py`
  - 5 个子命令：get / set / list / defaults / build-new-project
  - 24 个有效配置键 + 拼写建议（typo suggestion）
  - 支持 dotted path（如 `workflow.research`）读写
  - 自动类型解析（bool/int/float/string/null）
- **阶段域模块** — `scripts/cli/phase.py`
  - 6 个子命令：list / next-decimal / add / complete / find / status
  - 阶段状态推断（Pending → Planned → In Progress → Executed → Complete）
  - 数值排序、文件清点、ROADMAP.md 同步
- **路线图域模块** — `scripts/cli/roadmap.py`
  - 3 个子命令：get-phase / analyze / update-progress
  - 完整路线图解析：提取目标、成功标准、需求引用
  - 磁盘状态与路线图交叉验证
- **验证域模块** — `scripts/cli/verify.py`
  - 7 个子命令：summary / plan-structure / phase-completeness / consistency / health / commits / references
  - `health --repair` 模式自动修复缺失目录和配置
  - 文件引用解析、Git 提交验证、自检报告解析
- **模板域模块** — `scripts/cli/template.py`
  - 2 个子命令：fill（plan/summary/verification）/ select
  - 预填充 frontmatter + 中文模板（任务清单、验收标准、验证检查表）
  - 自动创建阶段目录
- **复合初始化模块** — `scripts/cli/init.py`
  - 8 个工作流初始化：execute-phase / plan-phase / new-project / quick / resume / verify-work / progress / todos
  - `_with_project_root()` — 自动注入项目根目录 + 代理安装状态 + 响应语言
  - HANDOFF.json 解析（next_steps / resume_files）
- **安全域模块** — `scripts/cli/security.py`
  - 4 个子命令：validate-path / scan-injection / validate-field / safe-json-parse
  - 路径遍历检测（`..` 阻断 + 项目边界验证）
  - 8 种提示注入模式检测 + Unicode 不可见字符扫描 + Base64 编码混淆检查
  - 字段名白名单验证（防止 STATE.md 注入）

### 来源融合
- **GSD** → gsd-tools.cjs 19 模块架构（state/phase/roadmap/config/verify/template/init/security/commands）→ Python 重实现
- **GSD** → `--raw` 机器可读输出 + `--cwd` 沙箱操作 + Windows 路径规范化
- **GSD** → 复合 init 命令一次性加载工作流所需全部上下文
- **ECC** → 安全检测（注入扫描 + Unicode 检测 + 路径遍历防护）

### 技术决策
- 选择 Python 而非 CJS，与现有 `scripts/engine/` 引擎层保持语言一致
- 域模块懒加载，CLI 启动时只导入 `cli.core` 和 `cli.router`
- 所有路径操作使用 `pathlib.Path`，原生 Windows 兼容

---

## [1.1.0] - 智能进化：画像 + 学习 + 子代理审查

### 新增
- **子代理驱动开发技能** — `skills/engineering/subagent-driven-development/`
  - `SKILL.md` — 每任务派发新鲜子代理 + 双阶段审查（规格合规 → 代码质量）
  - `implementer-prompt.md` — 实现者子代理提示模板（含 4 状态汇报协议）
  - `spec-reviewer-prompt.md` — 规格合规审查模板（独立验证，不信任汇报）
  - `code-quality-reviewer-prompt.md` — 代码质量审查模板（职责分离 + 测试质量）
- **开发者画像技能** — `skills/using-superopc/developer-profile/SKILL.md`
  - 8 维度模型：沟通风格/决策模式/调试方式/UX偏好/技术栈/摩擦触发/学习风格/解释深度
  - 6 问快速问卷系统 + 持续行为推断
- **观察钩子** — `scripts/hooks/observe.py`
  - PostToolUse 全局钩子，异步捕获工具使用元数据到 `~/.opc/learnings/observations.jsonl`
  - 自动提取工具名、行动类型、上下文、项目信息
- **代码库智能系统** — `/opc-intel` + `scripts/engine/intel_engine.py`
  - 4 种操作模式：query（关键词搜索）/ status（新鲜度检查）/ diff（快照对比）/ refresh（重建索引）
  - 5 个索引文件：stack.json / file-roles.json / api-map.json / dependency-graph.json / arch-decisions.json
  - `intel_engine.py` — 核心引擎（query/status/diff/write_intel/take_snapshot/validate）
  - `agents/opc-intel-updater.md` — 代码库分析代理（7步探索 + 输出预算 + 上下文质量分级）
- **融合蓝图** — `docs/FUSION-PLAN.md`
  - 9 大来源项目能力矩阵（56 项能力，34 已融合，22 未融合，61% 完成度）
  - P0/P1/P2 三级优先级排序 + v1.1.0 详细实施方案

### 增强
- **profile_engine.py** — 从骨架升级为可用
  - `generate_questionnaire()` — 6 问快速画像问卷
  - `apply_questionnaire_answers()` — 应用问卷结果
  - `export_markdown()` — 人可读 USER-PROFILE.md 输出
  - `save_markdown()` — 画像文档持久化
  - 维度描述映射（中文）
- **learning_store.py** — 新增观察管道（ECC Continuous Learning v2）
  - `record_observation()` — JSONL 原始观察写入
  - `detect_patterns()` — 工具使用模式检测（频率阈值）
  - `evolve_instincts()` — 模式自动升级为本能（高置信度学习条目）
  - `prune_observations()` — 过期观察清理（默认 30 天 TTL）
  - `stats()` — 新增观察计数
- **hooks.json** — 注册 `post:all:observe` 观察钩子
- **AGENTS.md** — 新增子代理驱动开发流水线 + opc-intel-updater 代理路由
- **parallel-agents/SKILL.md** — 新增与 subagent-driven-development 的交叉引用
- **continuous-learning/SKILL.md** — 新增自动化观察管道文档（数据流 + 本能演化 + 维护命令）
- **commands/opc/intel.md** — 从市场情报重构为代码库智能（query/status/diff/refresh）
- **scripts/engine/__init__.py** — 新增 intel_engine 模块声明

### 来源融合
- **Superpowers** → 子代理双阶段审查协议（implementer/spec-reviewer/code-quality-reviewer）
- **GSD** → 8 维度开发者画像 + 全局学习存储 + 代码库智能索引（功能90）
- **ECC** → 持续学习 v2 观察管道（observe → cluster → evolve）

---

## [1.0.0] - 正式发布

### 新增
- **4 个项目模板** — `templates/projects/`
  - `saas-starter/` — Next.js 14 + Supabase + Stripe 全栈 SaaS 模板（README + project/requirements/roadmap/config）
  - `api-service/` — .NET 8 Minimal API + PostgreSQL API 服务模板
  - `mobile-app/` — Kotlin + Jetpack Compose Android 原生应用模板
  - `landing-page/` — Next.js 14 静态导出营销页模板（轻量 coarse 粒度配置）
- **3 个使用示例** — `examples/`
  - `01-saas-mvp-workflow/` — 从零到上线的 SaaS MVP 完整工作流演示
  - `02-api-development/` — .NET 8 API 从设计到部署的工作流演示
  - `03-business-workflow/` — 商业技能在产品验证、定价和增长中的应用
- **英文文档** — `README_EN.md`
  - 完整英文版 README，覆盖安装、架构、快速开始、技能一览、设计原则
  - 中文 README 添加英文版链接
- **社区建设文件**
  - `CODE_OF_CONDUCT.md` — Contributor Covenant 2.1 中英双语行为准则
  - `.github/ISSUE_TEMPLATE/bug_report.md` — 结构化 Bug 报告模板
  - `.github/ISSUE_TEMPLATE/feature_request.md` — 功能建议模板（含一人公司价值维度）
  - `.github/PULL_REQUEST_TEMPLATE.md` — PR 模板（含检查清单）
  - `.github/DISCUSSION_TEMPLATE/ideas.yml` — Discussion 想法分享模板
  - `docs/building-in-public.md` — Building in Public 教程（内容来源映射 + 日历模板）
  - `docs/contributor-rewards.md` — 贡献者奖励机制（4 等级 + 积分体系）
  - `docs/community-guide.md` — 社区指南（渠道 + 活动 + 获取帮助）

### 变更
- 更新 `README.md` 添加项目模板、示例和英文版链接，路线图表格标记 v1.0.0 为当前版本
- 更新 `ROADMAP.md` 标记 v1.0.0 所有子项已完成
- 更新 `.claude-plugin/plugin.json` 到 `1.0.0`

### 质量标准达成
- 51 个技能全部包含压力测试区块
- 完整双语文档（中文 README + 英文 README_EN.md）
- CI/CD 覆盖 pytest + repo health + convert smoke + release 打包
- 4 个项目模板 + 3 个使用示例
- 11 个 AI 工具适配（Claude Code / Cursor / Windsurf / Copilot / Gemini CLI / OpenCode / Codex / Trae / Cline / Augment / OpenClaw）

---

## [0.9.0] - 完成

### 新增
- **共享 QA 引擎** — `scripts/opc_quality.py` + `scripts/opc_health.py`
  - 项目模式检查 `.opc/` 核心文件、支撑目录、`config.json`、`HANDOFF.json`、需求覆盖、VERIFICATION 配对、声明溯源与 SUMMARY 追踪字段
  - 仓库模式检查 frontmatter、plugin/hook 接线、内部 markdown 链接、GitHub Actions 与版本元数据
  - `--repair` 支持补齐确定性缺失结构，并输出结构化 JSON 结果供后续 CI / 命令消费
- **健康检查命令** — `commands/opc/health.md`
  - 暴露 `/opc-health` 作为 v0.9.0 质量保证体系入口
  - 支持 project / repo / all 三种目标范围
- **验证模板** — `templates/verification.md`
  - 为 SUMMARY 之外的验证证据提供统一格式
- **技能压力测试契约** — `skills/**/SKILL.md`
  - 全量技能补齐 `## 压力测试` 区块
- **GitHub Actions** — `.github/workflows/quality.yml` + `.github/workflows/release.yml`
  - 覆盖 pytest、repo health、convert smoke 与 release 打包

### 变更
- 更新 `templates/config.json`、`phase-prompt.md`、`summary.md`、`requirements.md`、`state.md`，增加 v0.9.0 质量字段与可追溯性锚点
- 更新 `references/gates.md` 与 `references/verification-patterns.md`，同步 health / traceability / node repair 语义
- 更新 `README.md`、`CLAUDE.md`、`ROADMAP.md`，并将插件版本升级到 `0.9.0`
- 更新 `tests/test_session_workflow.py`，覆盖 repo health 与 repair scaffolding 回归

---

## [0.8.0] - 完成

### 新增
- **会话工作流层** — `scripts/opc_workflow.py` + `scripts/opc_progress.py` + `scripts/opc_pause.py` + `scripts/opc_resume.py` + `scripts/opc_session_report.py` + `scripts/opc_next.py`
  - 基于现有 `.opc/STATE.md` / `ROADMAP.md` / `REQUIREMENTS.md` 生成 progress、resume、report 与 next 建议
  - 支持写入 `.opc/HANDOFF.json` 并同步更新 `STATE.md` 的会话连续性字段
  - 聚合 `.opc/sessions/*.json` 与 `.opc/audit.log` 形成会话报告
- **13 个 v0.8 命令** — `commands/opc/progress.md` + `pause.md` + `resume.md` + `session-report.md` + `next.md` + `autonomous.md` + `fast.md` + `discuss.md` + `explore.md` + `thread.md` + `seed.md` + `backlog.md` + `do.md`
- **5 个 v0.8 参考/技能文档** — `references/session-management.md` + `references/workflow-modes.md` + `references/context-threads.md` + `skills/using-superopc/session-management/SKILL.md` + `skills/using-superopc/workflow-modes/SKILL.md`
- **兼容会话参考文档** — `references/session-workflows.md` + `references/handoff-format.md`
- **交接模板** — `templates/handoff.json`

### 变更
- 更新 `README.md` 添加 v0.8 会话命令、脚本入口、上下文线程参考，并同步技能/命令总数与命令树
- 更新 `ROADMAP.md` 标记 v0.8.0 会话管理、高级工作流与上下文线程子项完成
- 更新 `.claude-plugin/plugin.json` 到 `0.8.0`
- 重新生成 `integrations/`，同步新命令与插件版本元数据

---

## [0.7.0] - 完成

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
- **插件清单** — `.claude-plugin/plugin.json`
- **Marketplace 模板** — `templates/marketplaces/superopc-marketplace/`
- **路线图** — `ROADMAP.md`（v0.1.0 到 v2.0.0，480 行）
- **许可证** — MIT
