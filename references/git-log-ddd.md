# SuperOPC Git Log - DDD 功能模块驱动重整

生成日期：2026-04-29

来源命令：`git log --all --decorate --date=iso --pretty=fuller`

覆盖范围：
- 原始提交数：180
- 原始日志行数：7636
- 当前主线：`main` / `origin/main`
- 整理时 HEAD：`270eb0b refactor: 保留核心 SuperOPC 运行面`

说明：
- 本报告不是按时间顺序复述 commit，而是按 DDD 的“限界上下文 / 功能模块 / 领域能力”重组。
- 历史中存在大量中文/英文镜像提交、重写历史、标签引用、worktree 引用和 stash 引用。这里将它们视为同一领域事件的多个提交证据。
- “模块演进”优先描述业务能力变化；短哈希用于追溯原始 git 记录。

## 1. DDD 限界上下文总览

SuperOPC 的提交历史可以重整为 12 个主要限界上下文：

| DDD 层级 | 限界上下文 | 核心职责 | 代表路径 |
|---|---|---|---|
| Core Domain | 产品交付工作流 | 从想法到规划、实现、审查、发布的主业务闭环 | `agents/opc-{planner,executor,reviewer,shipper,verifier}.md`, `skills/product/*` |
| Core Domain | 代理编排与注册 | 代理能力建模、路由、派发、协作协议 | `agents/`, `agents/registry.json`, `scripts/engine/dag_engine.py` |
| Core Domain | Skill Dispatcher | 将用户意图映射到 dispatcher skill，再派发 agent workflow | `skills/`, `skills/registry.*`, `scripts/engine/skill_dispatcher.py` |
| Supporting Domain | 命令入口与 CLI Runtime | `/opc-*` slash 命令、`opc-tools` CLI、本地 runtime 白名单 | `commands/opc/*`, `bin/opc-tools`, `scripts/cli/*` |
| Supporting Domain | 自主运行引擎 | 事件、决策、DAG、巡航、调度、状态循环 | `scripts/engine/{event_bus,decision_engine,dag_engine,cruise_controller,state_engine}.py` |
| Supporting Domain | 会话 / 状态 / 上下文 | pause/resume/progress/report、HANDOFF、线程、状态连续性 | `templates/*`, `scripts/opc_{pause,resume,progress,session_report}.py`, `references/*handoff*` |
| Supporting Domain | 质量门控与验证 | hooks、health、lint、测试、CI、安全检查、验证循环 | `hooks/`, `scripts/hooks/*`, `scripts/opc_health.py`, `tests/` |
| Supporting Domain | 情报与学习 | research、intel、profile、observation、learning store、方法论库 | `scripts/intelligence/*`, `scripts/engine/{profile_engine,learning_store,intel_*}.py` |
| Supporting Domain | 商业咨询 | Anti-Build-Trap、商业 playbook、SEO/content/growth/pricing domain agents | `agents/opc-business-advisor.md`, `agents/domain/*`, `references/business/*` |
| Infrastructure | 多运行时分发与转换 | 插件 marketplace、Claude/Gemini/Cursor/Windsurf 等导出 | `scripts/convert*.py`, `.claude-plugin` 历史, `integrations/` 历史 |
| Infrastructure | 文档与知识库 | README/AGENTS/CLAUDE/ROADMAP/CHANGELOG/ADR/cheat sheet | `README.md`, `AGENTS.md`, `CLAUDE.md`, `references/*` |
| Infrastructure | 仓库治理与瘦身 | 版本标签、历史重写、死代码删除、核心运行面保留 | tags, cleanup commits, refactor commits |

## 2. 领域时间线：按业务能力，而不是按 commit 日期

### 2.1 产品从“骨架”变成“可运行操作系统”

领域事件：
1. 建立 SuperOPC 初始骨架：skills、agents、commands 三层最小闭环。
2. 加入质量门控、规则、引用资料、多工具转换。
3. 扩展代理数量并支持波次并行。
4. 补齐状态、模板、工程技能、商业技能、运行时导出。
5. 发布 v1.0.0，并在之后进入智能进化、CLI、v2 engine、dispatcher pattern、command contract 阶段。

提交证据：
- `f38f563`, `f94de41`, `8a1449c`：初始化仓库。
- `8117bb5`, `e9f2151`, `c542dba`：核心骨架，24 skills + 6 agents + 7 commands。
- `dc6840c`, `340fad7`, `07d4ac4`：质量门控、rules、references、多工具转换。
- `02d28ca`, `fc5797a`, `8ffd87a`：代理扩展到 15 个，加入波次并行执行。
- `858379d`, `0ee1e99`, `ca3e6e6`：状态管理、文件系统、模板系统。
- `fc819c2`, `4fc00cb`, `37e2c25`：工程技能深化。
- `7db5e06`, `80c1d97`：商业技能和 dashboard。
- `d1dc4a6`, `9db94ea`, `407b3aa`：v1.0.0 发布与 CI 修正。

### 2.2 架构从“很多技能”收敛为“dispatcher skill + agent workflow”

领域事件：
1. v1.3 以前：skills 同时承载入口、流程、知识。
2. v1.3：提出 skill-dispatcher / agent-workflow 架构重构。
3. v1.4：技术栈、商业、review、skill authoring 等知识下沉到 references；skill 瘦身为 dispatcher；agent 成为 workflow source of truth。
4. v1.4.1：用 registry、intent router、skill frontmatter，把派发从隐式文本规则升级为可验证的元数据。
5. v1.4.2：用命令契约 lint 和白名单分层封堵 slash command 漏洞。

提交证据：
- `5f1170c`, `4ae82c9`, `46709b2`：制定 skill-dispatcher / agent-workflow 重构计划。
- `271a574`, `ec79482`：planning 路径落地 dispatcher / agent workflow。
- `a274e0b`, `8a43650`：build / review / ship 套用 dispatcher pattern。
- `7cd655b`, `e510f9b`：原子技能合并与 mode 路由命令收敛。
- `c18feb6`, `63eb910`：技术栈 patterns 下沉到 references。
- `395a301`, `eb327e0`：商业方法论下沉到 references/business。
- `adb029c`, `11306fb`：intelligence 参考化，autonomous-ops 归入元层。
- `e1d8d59`, `280a069`：code-review-pipeline 合入 review-rubric。
- `fe739b4`, `ed20815`：brainstorming 合并到 planning。
- `a55696e`, `f085dc8`：business/advisory、security-review、debugging dispatcher 新建和瘦身。
- `c60ab41`, `310c1ba`：Skill Registry JSON schema。
- `6afb0e2`, `b1a7cce`：17 份 SKILL.md frontmatter 扩展。
- `edee94e`, `e3de11f`：Skill Registry 生成器。
- `d8b19ad`, `db9832a`：Intent Router L1+L3。
- `47ecb59`, `68cd381`：新增命令并通过 lint 强制 command contract。
- `c98ea18`, `5006d33`：白名单拆分为 PURE 与 MIXED 两档。

### 2.3 命令入口从“脚本集合”变成“契约化入口层”

领域事件：
1. 最初提供 `/opc-start`、`/opc-plan`、`/opc-build`、`/opc-review`、`/opc-ship` 等产品交付入口。
2. v1.2 加入 `opc-tools` CLI，把 GSD 风格本地工具层 Python 化。
3. v1.4.2 明确命令分层：dispatcher command、local runtime command、mixed low-friction command。
4. 对 session/cruise 类命令进行 dispatcher 化，避免 slash 命令直接绕过 workflow。
5. 对 `/opc-start`、Anti-Build-Trap、错误路径、quick-start 文档做同步。

提交证据：
- `8117bb5`, `e9f2151`, `c542dba`：初始 7 个 slash commands。
- `062ce43`, `219b9a7`：`opc-tools` CLI 工具层。
- `ed3300a`, `9bf1a44`：profile / research / intel 主路径接线。
- `cbf27d2`, `b7c7418`：7 个 session/cruise commands 经 dispatcher skill 路由。
- `47ecb59`, `68cd381`：新增 `/opc-debug`、`/opc-security`、`/opc-business`。
- `81f9fa5`, `b8ee260`：澄清 `/opc-start` 派发分支和 Anti-Build-Trap。
- `793e3b1`, `d2e9885`：README quick-start 第 3-15 步改为 slash 命令入口。
- `ab3a237`, `6e1d811`：ADR-0004 command contract enforcement。

### 2.4 自主运行从“概念”变成“事件驱动引擎”

领域事件：
1. 建立 v2 autonomous engine：event bus、decision engine、DAG engine、state engine、scheduler、notification。
2. 将 engine 与 hooks、cruise、tests、CI 集成。
3. 加入巡航入口、heartbeat、自主推进边界。
4. v1.4.2 修复 cruise fake dispatch：PLAN/BUILD/REVIEW/DEBUG/SHIP 必须派发真实 agent，而不是只读 progress。
5. 后续保持 state continuity，并隔离 event bus，防止跨项目/跨会话污染。

提交证据：
- `e61bdfb`, `f17c429`：构建 v2 自主运营引擎。
- `4e988d2`, `2da4485`：M7 融合集成，贯通 workflow + hooks + cruise + tests + CI。
- `1f0e389`, `2b369fd`：补完 v0.8.0 自主推进入口和发布对齐。
- `266659b`, `9ae171c`：引入 `opc-cruise-operator`，autonomous-ops 升级为 dispatcher。
- `35e0718`, `c43d994`：cruise 派发真实 agents，替代 fake progress calls。
- `2e3e310`, `7b9904c`, `d6a0d4f`, `138697a`：`opc_routing_stats` 观察期工具和契约测试。
- `672298d`, `f78cdb3`：保持状态连续性并隔离 event bus。

### 2.5 会话与状态从“模板”扩展为“跨会话协议”

领域事件：
1. v0.4 引入 config/project/requirements/state/roadmap/phase/summary/debug 模板。
2. v0.8 加入 session workflow、context threads。
3. v1.4.2 把 session-management 从 meta skill 升级为 dispatcher，绑定 `opc-session-manager`。
4. 命令入口包含 pause/resume/progress/session-report，HANDOFF JSON 成为跨机器/跨会话协议。
5. 后续修复 init new-project 与 nested directory 的 `.opc` 边界。

提交证据：
- `858379d`, `0ee1e99`, `ca3e6e6`：状态管理 + 模板系统。
- `9de587a`, `0691bc6`：会话工作流与上下文线程层。
- `266659b`, `9ae171c`：引入 `opc-session-manager`，session-management 升级为 dispatcher。
- `cbf27d2`, `b7c7418`：session/cruise commands dispatcher 化。
- `93000b9`, `0ce457f`：标记旧 session references 为 deprecated，修正 README hook catalog。
- `cc666f4`：强化 new-project 初始化和 runtime handoff。
- `aef1a4a`, `c6871db`：对齐 init todo schema 与 runtime lint。

### 2.6 质量体系从“hook 提醒”升级为“可验证契约”

领域事件：
1. v0.2 引入 hooks、rules、security、testing、git workflow。
2. v0.9 加入 `/opc-health` 和质量保证体系。
3. CI 从部分测试扩展到完整 `tests/`。
4. 增加 command contract lint、skill registry consistency、routing stats tests。
5. 删除失效断言和硬编码版本号，保持测试矩阵真实。

提交证据：
- `dc6840c`, `340fad7`, `07d4ac4`：hooks + rules + references + converter。
- `85e4117`, `a578150`：v0.9.0 质量保证体系与 `/opc-health`。
- `55d1ab4`, `079228b`：修复 CI workflow 路径前缀和测试版本断言。
- `407b3aa`, `3efac31`：health check 改用 semver 校验。
- `851c8c5`, `9086b29`：registry 生成器契约测试。
- `6f3f222`, `664d604`：intent router 契约测试。
- `b4312b2`, `1be5f24`：health 加入 skill-registry-consistency。
- `31db21d`, `9a8451d`：CI 扩展到完整 `tests/`，并记录 intent_router v1.5 对接任务。
- `9b24952`, `754c823`：修复 convert_all runtime metadata 测试硬编码。

### 2.7 情报与学习能力形成独立 supporting domain

领域事件：
1. 早期提供 market-research、follow-builders 等 intelligence skills。
2. v1.1 引入 developer profile、learning pipeline、codebase intelligence、marketing assets。
3. v1.2/后续 CLI 主路径接入 profile、research、intel。
4. v1.4 将 intelligence 技能转为 references，由 researcher / intel-updater / runtime 消费。
5. 修复调度任务输出目录，使情报产物写到项目级 `.opc`。

提交证据：
- `7c61a05`, `f88bd4d`：智能进化层，包含画像、学习管道、代码库智能。
- `de7875a`, `ff95100`：九大项目差距补全，含领域代理、学习闭环、多源情报、技能提取、方法论库。
- `ed3300a`, `9bf1a44`：profile / research / intel 运行入口与上下文闭环。
- `df59c5f`, `6c0e2da`：调度任务写入项目级 intelligence 输出目录。
- `533d106`, `ecd9da5`：observe.py 追加 skill 路由同步。
- `adb029c`, `11306fb`：intelligence 参考化。

### 2.8 商业咨询从“技能清单”收敛为“business advisor + domain agents”

领域事件：
1. 初始版本含 10 个 business skills。
2. v0.6 深化商业技能和 dashboard。
3. v1.4 商业方法论下沉到 `references/business/`。
4. 增加 `opc-business-advisor`，统一商业 workflow，并委派 SEO/content/growth/pricing 等 domain agents。
5. v1.4.2 给 `/opc-business` 加入 command contract，并将 Anti-Build-Trap 纳入入口说明。

提交证据：
- `8117bb5`, `e9f2151`, `c542dba`：初始 10 个商业技能。
- `7db5e06`, `80c1d97`：商业技能深化 + dashboard。
- `395a301`, `eb327e0`：商业方法论下沉到 references/business。
- `3a9ca23`, `142aff7`：新增 `opc-business-advisor` 统一商业活动 workflow。
- `a55696e`, `f085dc8`：business/advisory dispatcher 新建与瘦身。
- `47ecb59`, `68cd381`：新增 `/opc-business` 并纳入 command contract lint。
- `81f9fa5`, `b8ee260`：Anti-Build-Trap 与错误路径说明。

### 2.9 分发与转换从“多工具导出”变成“运行时契约”

领域事件：
1. v0.2 引入多工具转换。
2. v0.7 支持 MCP 模板层和 10+ runtime exports。
3. v1.0 校正插件 marketplace 分发模型。
4. v1.4 同步 plugin 元数据。
5. v1.4.2 修复 converter 把 skill prompt asset 误判成 skill 的问题，明确 flat runtime 的资产限制。
6. 最新 cleanup 删除可再生输出、示例、营销、网站、MCP 模板，仅保留核心运行面。

提交证据：
- `dc6840c`, `340fad7`, `07d4ac4`：多工具格式转换。
- `1ff2189`, `218afe4`：MCP 模板层与 10+ runtime export。
- `f4c2e50`, `b0f8c69`：校正插件与 marketplace 分发模型。
- `971f607`, `938cd9c`：同步 v1.4.0 plugin 元数据。
- `01cc77e`, `6aca41c`：plugin 版本 1.4.0 -> 1.4.2，补注册 2 个 core agents。
- `b7cfbcb`, `c0a2bc6`：converter 只收集 `SKILL.md`，不再误判 prompt assets。
- `270eb0b`：精简仓库到核心运行面，移除可再生/非核心内容。

### 2.10 文档知识库承担“架构契约”和“迁移记录”

领域事件：
1. README/AGENTS/CLAUDE/ROADMAP/CHANGELOG 记录版本、架构、命令、hook、skill 迁移。
2. v1.3/v1.4 使用 plan/ADR/roadmap 记录 dispatcher pattern 和 skill slim 迁移。
3. v1.4.2 补齐命令契约断层、quick-start、cheat sheet、session docs deprecated。
4. 最新 cleanup 删除历史 docs，保留运行入口和必要 references。

提交证据：
- `a9ff097`, `52ea6f6`：校正文档与 hook 描述。
- `807bc70`, `f3e20e1`：修复 README 无效链接。
- `d8a3ce3`, `69372e3`：发布文案与社区投放素材。
- `356be5b`, `88a2cb6`：同步架构重构叙述到入口文档与 CHANGELOG。
- `294e05e`, `1108125`：制定 v1.4.0 skill 精简计划。
- `84f00e1`, `403ce2f`：v1.4.1 Phase A 设计、ADR、PLAN、ROADMAP 打标。
- `1488880`, `577cef9`：v1.4.1 CHANGELOG + ROADMAP 收尾。
- `780de2e`, `3b502e3`：v1.4.2 Phase B 实施计划草稿。
- `ef0790e`, `a16b9ff`：README 同步到 v1.4.2。
- `e8d4d7a`, `1b1fd75`：CLAUDE 同步到 v1.4.2。
- `63bc918`, `2bdb897`：AGENTS 增补 v1.4.2 command contract 迁移表。
- `ad2bb93`, `f3ff323`：命令决策树与 ROADMAP/CHANGELOG source-of-truth 说明。
- `93000b9`, `0ce457f`：session reference deprecated 与 README hook catalog 修正。

## 3. 模块驱动的最终形态

### 3.1 核心业务模块：Product Delivery

职责：
- 把用户需求转为计划、实现、审查、验证、发布。
- 由 `opc-planner`、`opc-executor`、`opc-reviewer`、`opc-verifier`、`opc-shipper` 分别持有 workflow。
- Product skills 变为轻量 dispatcher，不再承载完整业务流程。

历史结论：
- 早期版本把“方法论 + 执行流程 + 入口”混在 skill 中。
- v1.3/v1.4 后，workflow source of truth 移到 agent；skill 只负责识别场景和派发。
- 这让功能模块更接近 DDD：业务能力由 agent 聚合持有，入口层和参考资料分离。

### 3.2 核心编排模块：Agent Orchestration

职责：
- 建模 agent capability。
- 根据任务场景、capability_tags、registry、intent router 派发 agent。
- 支持波次并行、fallback、真实 runtime dispatch。

历史结论：
- 从 6 个初始 agents 扩展到 27 个注册 agents。
- 从“靠文档约定派发”演进到 registry + route stats + command lint。
- cruise 假派发 bug 被修正后，运行时 dispatch 才真正闭环。

### 3.3 核心入口模块：Command Runtime

职责：
- 统一 slash command 和本地 CLI 入口。
- 区分 dispatcher command、local runtime command、mixed low-friction command。
- 用 lint 保证命令不绕过 workflow。

历史结论：
- `/opc-*` 入口由“直接脚本/说明文档”逐步变成“受契约约束的应用服务层”。
- v1.4.2 是该模块的关键转折点：命令契约开始由测试强制，而不是只靠 AGENTS/README 描述。

### 3.4 支撑模块：State / Session / Context

职责：
- 保存项目状态、会话连续性、HANDOFF、线程、backlog、seed。
- 支持暂停、恢复、进度、报告。
- 支撑 autonomous loop 和跨机器协作。

历史结论：
- 状态最初是模板系统的一部分。
- v0.8 以后成为独立 session workflow。
- v1.4.2 以后由 `opc-session-manager` 持有权威流程。

### 3.5 支撑模块：Quality / Verification / Safety

职责：
- hooks、rules、security、testing、health、CI、lint、verification loop。
- 用自动化验证替代口头约定。

历史结论：
- 质量体系从 v0.2 的 hook/rule 提醒起步。
- v0.9 `/opc-health` 让健康检查产品化。
- v1.4.1/v1.4.2 让 registry、intent router、command contract 都有测试保护。

### 3.6 支撑模块：Business / Intelligence

职责：
- Business advisor 处理商业策略和 Anti-Build-Trap。
- Intelligence subsystem 处理市场研究、开发者画像、学习闭环、代码库情报。

历史结论：
- 早期 business/intelligence 是技能清单。
- 后续被拆成：advisor/domain agent 持有流程，references 持有方法论，runtime/CLI 持有执行入口。

### 3.7 基础设施模块：Distribution / Documentation / Repo Hygiene

职责：
- 转换到多 AI runtime。
- 维护插件分发元数据。
- 记录架构契约、版本路线图、迁移说明。
- 保持仓库只承载核心运行面。

历史结论：
- 仓库曾包含示例、营销、网站、历史 docs、MCP 模板和可再生输出。
- 最新 HEAD 明确收敛：主仓库只保留 agent、skill、command、runtime、规则、模板、测试和 CI。

## 4. 版本里程碑按 DDD 模块重排

| 版本 / 阶段 | 主要领域能力 | 关键模块 |
|---|---|---|
| v0.1.0 | 核心骨架：skills + agents + commands | Product Delivery, Agent Orchestration, Command Runtime |
| v0.2.0 | 质量门控与多工具转换 | Quality, Distribution |
| v0.3.0 | 代理扩展与波次并行 | Agent Orchestration |
| v0.4.0 | 状态、文件系统、模板 | State / Session |
| v0.5.0 | 工程技能深化 | Skill / Engineering References |
| v0.6.0 | 商业技能与 dashboard | Business Advisory |
| v0.7.0 | MCP 模板与 runtime export | Distribution |
| v0.8.0 | 会话工作流、自主推进入口 | Session, Autonomous Ops |
| v0.9.0 | `/opc-health` 与质量体系 | Quality / Verification |
| v1.0.0 | 正式发布、模板、示例、双语文档 | Release / Documentation |
| v1.1.0 | 智能进化层 | Intelligence / Learning |
| v1.2.0 | `opc-tools` CLI | Command Runtime |
| v2 engine / M7 | 事件驱动 autonomous engine | Autonomous Runtime |
| v1.3 | skill-dispatcher / agent-workflow | Architecture / Product Delivery |
| v1.4 | skill 精简、references 层、business advisor | Skill Dispatcher, References, Business |
| v1.4.1 | skill registry、intent router、health consistency | Routing, Quality |
| v1.4.2 | command contract、session/cruise dispatcher、real dispatch | Command Runtime, Autonomous Ops |
| 2026-04-23 | runtime workflow/docs 精简，state continuity 修复 | Runtime, State |
| 2026-04-27 | new-project init 与 runtime handoff 修复 | CLI Runtime, State |
| 2026-04-28 | 核心运行面瘦身 | Repo Governance |

## 5. 提交覆盖索引（按模块）

### Product Delivery / Agents / Workflow

- `8117bb5`, `e9f2151`, `c542dba`：核心骨架，6 agents + product commands。
- `02d28ca`, `fc5797a`, `8ffd87a`：代理扩展到 15 个。
- `271a574`, `ec79482`：planning dispatcher / agent workflow。
- `a274e0b`, `8a43650`：build / review / ship dispatcher pattern。
- `1ea0bda`, `d747c7a`：reviewer 吸收 Quick/Standard/Deep。
- `64851c9`, `577a1bd`：debugger 吸收修复规程。
- `7d89daf`, `26e3e9c`：security auditor 吸收 OWASP workflow。
- `266659b`, `9ae171c`：session manager / cruise operator。

### Skill Dispatcher / References

- `fc819c2`, `4fc00cb`, `37e2c25`：工程技能深化。
- `5f1170c`, `4ae82c9`, `46709b2`：架构重构计划。
- `7cd655b`, `e510f9b`：原子技能合并与 mode 路由命令收敛。
- `c18feb6`, `63eb910`：技术 patterns 下沉。
- `395a301`, `eb327e0`：business references 下沉。
- `adb029c`, `11306fb`：intelligence 参考化。
- `6f34153`, `cf3b9a0`：skill-authoring 合并参考手册。
- `e1d8d59`, `280a069`：review-rubric 合并。
- `fe739b4`, `ed20815`：brainstorming 合并 planning。
- `a55696e`, `f085dc8`：dispatcher 新建与瘦身。
- `c60ab41`, `310c1ba`, `6afb0e2`, `b1a7cce`, `edee94e`, `e3de11f`：skill registry schema / frontmatter / generator。

### Command Runtime / CLI

- `062ce43`, `219b9a7`：`opc-tools` CLI。
- `ed3300a`, `9bf1a44`：profile / research / intel CLI 接线。
- `cbf27d2`, `b7c7418`：session/cruise commands dispatcher 化。
- `47ecb59`, `68cd381`：新增 debug/security/business commands。
- `c98ea18`, `5006d33`：command whitelist 分层。
- `81f9fa5`, `b8ee260`：`/opc-start` 分支与 Anti-Build-Trap。
- `793e3b1`, `d2e9885`：quick-start slash command 化。
- `ab3a237`, `6e1d811`：ADR-0004 command contract。
- `cc666f4`：新项目 init 与 runtime handoff 强化。

### Autonomous Runtime / Routing

- `e61bdfb`, `f17c429`：v2 autonomous engine。
- `4e988d2`, `2da4485`：engine 与 workflow/hooks/cruise/tests/CI 集成。
- `1f0e389`, `2b369fd`：自主推进入口与发布对齐。
- `d8b19ad`, `db9832a`：Intent Router L1+L3。
- `35e0718`, `c43d994`：cruise 真实派发。
- `2e3e310`, `7b9904c`, `d6a0d4f`, `138697a`：routing stats 工具与测试。
- `7d81592`, `7b31610`：删除 deprecated dag_runner，同步 engine docstring。
- `672298d`, `f78cdb3`：状态连续性与 event bus 隔离。

### State / Session / Context

- `858379d`, `0ee1e99`, `ca3e6e6`：状态与模板系统。
- `9de587a`, `0691bc6`：会话工作流与上下文线程。
- `266659b`, `9ae171c`：session manager。
- `93000b9`, `0ce457f`：旧 session docs deprecated。
- `aef1a4a`, `c6871db`：init todo schema 与 runtime lint。

### Quality / Security / Verification

- `dc6840c`, `340fad7`, `07d4ac4`：hooks/rules/references/converter。
- `85e4117`, `a578150`：质量保证体系与 `/opc-health`。
- `55d1ab4`, `079228b`, `407b3aa`, `3efac31`：CI 和 semver 修复。
- `851c8c5`, `9086b29`, `6f3f222`, `664d604`：registry/router RED tests。
- `b4312b2`, `1be5f24`：health registry consistency。
- `31db21d`, `9a8451d`：CI 跑完整 tests。
- `9b24952`, `754c823`：runtime metadata 测试修复。

### Business / Intelligence

- `7db5e06`, `80c1d97`：商业技能与 dashboard。
- `7c61a05`, `f88bd4d`：智能进化层。
- `de7875a`, `ff95100`：领域代理、学习闭环、多源情报、方法论库。
- `3a9ca23`, `142aff7`：business advisor。
- `df59c5f`, `6c0e2da`：intelligence 输出目录修复。
- `533d106`, `ecd9da5`：observe skill routing sync。

### Distribution / Conversion / Plugin

- `dc6840c`, `340fad7`, `07d4ac4`：多工具转换。
- `1ff2189`, `218afe4`：MCP 模板层与 runtime export。
- `f4c2e50`, `b0f8c69`：marketplace 分发模型。
- `971f607`, `938cd9c`：plugin 元数据同步。
- `01cc77e`, `6aca41c`：plugin 版本和 core agent 注册。
- `b7cfbcb`, `c0a2bc6`：converter skill asset 分类修复。

### Documentation / Governance / Cleanup

- `a9ff097`, `52ea6f6`, `807bc70`, `f3e20e1`：文档修正。
- `356be5b`, `88a2cb6`, `294e05e`, `1108125`, `84f00e1`, `403ce2f`, `1da2ff4`, `50d23cc`, `780de2e`, `3b502e3`：计划/ADR/ROADMAP/执行摘要。
- `006e6af`, `b79cf48`, `4285054`, `31796da`：v1.4 元文档同步与收尾。
- `4f1b693`, `fec8486`：using-superopc v1.4.1 加速路径。
- `1488880`, `577cef9`：v1.4.1 CHANGELOG + ROADMAP。
- `ef0790e`, `a16b9ff`, `e8d4d7a`, `1b1fd75`, `63bc918`, `2bdb897`, `ad2bb93`, `f3ff323`：v1.4.2 README/CLAUDE/AGENTS/cheat-sheet 同步。
- `0b0fbab`, `3419dad`：精简 runtime workflows 与 docs。
- `270eb0b`：保留核心 SuperOPC 运行面。

### Branch / Tag / Rewrite / Stash Evidence

- 标签：`v0.1.0` 到 `v1.0.0`，以及 `pre-refactor-v1.3`, `pre-refactor-v1.4`。
- 分支：`main`, `fix-real-usage-flow-20260427`, `backup/history-before-chinese-titles-20260423`, 多个 worktree 分支。
- stash：`18bcac3`, `56ef30e`, `1aabfae`，保留 pre-rewrite-v0.6.0 相关状态。

## 6. 给后续维护者的 DDD 解读

后续读 git log 时，不应把 SuperOPC 视为“脚本仓库”或“prompt 集合”。提交历史显示它的真实领域模型是：

1. `Command Runtime` 接收用户意图。
2. `Skill Dispatcher` 做轻量识别和派发。
3. `Agent Workflow` 持有业务流程。
4. `References` 持有方法论知识。
5. `Runtime Engine` 处理自动化、状态、事件和 DAG。
6. `Quality Gate` 用测试、lint、health、hooks 约束演化。
7. `Distribution` 把同一领域模型转换到不同 AI runtime。

当前 HEAD 的方向是明确的：主仓库只保留核心运行面；示例、营销、历史 docs、可再生输出和模板导出不应重新混回核心领域。
