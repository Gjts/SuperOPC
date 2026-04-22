# ADR-0004: 命令契约强制——slash 命令必须派发 dispatcher skill（含只读白名单例外）

**日期**: 2026-04-22
**状态**: accepted
**决策者**: 项目 owner
**关联**:
- `AGENTS.md` §架构契约
- `ADR-0001` Skill Registry Schema（dispatcher 需声明 `dispatches_to`）
- `scripts/verify_command_contract.py`（lint 实现）
- `scripts/engine/cruise_controller.py`（P0 修复的源头）

## 背景

v1.3/v1.4 确立了三层契约：`Command → Dispatcher Skill → Agent`。但架构审计发现 3 处**系统性**的契约断层：

**断层 1：Cruise controller 假派发**
`scripts/engine/cruise_controller._dispatch_command` 把 `ActionType.PLAN / BUILD / REVIEW`
全部路由到 `python scripts/opc_workflow.py progress`——一个纯**只读**状态查询。也就是说 cruise 模式宣称"自动规划/构建/审查"，实际只刷新了一次面板。规划/执行/审查 agent 完全**没有被派发过**。

**断层 2：命令层越过 skill 层**
16 个 slash 命令的 `## 动作` 段落直接写 `python scripts/xxx.py`，跳过 dispatcher skill：
- 会话类：`/opc-pause` `/opc-resume` `/opc-progress` `/opc-session-report`
- 巡航类：`/opc-cruise` `/opc-heartbeat` `/opc-autonomous`
- 白名单只读类：`/opc-health` `/opc-dashboard` `/opc-stats` `/opc-intel` `/opc-profile` `/opc-backlog` `/opc-seed` `/opc-thread` `/opc-research`

前 7 个是**真的违规**（有状态变更、agent 职责），后 9 个是**合理的只读 CLI**，但契约没明确说它们豁免。

**断层 3：Meta skill 被显式 slash 触发却无 agent 绑定**
`session-management` 和 `autonomous-ops` 被标记为 meta（系统级规则），但 7 个 slash 命令都应该派发它们。它们的 frontmatter 缺 `dispatches_to` 字段，没有 agent 承载 workflow——导致无论从命令层还是 skill 层都派不出 agent。

核心问题：**契约只在文档里存在，没有任何机械强制**，演进中很容易出现隐形违规。

## 决策

采用**"双向约束 + 机械强制"**策略：

### 1. 新建两个 workflow 持有 agent
- `agents/opc-session-manager.md`：持有 pause/resume/progress/session-report 四个子场景的完整 workflow
- `agents/opc-cruise-operator.md`：持有 cruise-start/heartbeat/autonomous-advance 三个子场景的完整 workflow（含 HARD-GATE：Anti-Build-Trap + RED 动作拦截 + 失败阈值）

### 2. 升级 meta skill → dispatcher
- `skills/using-superopc/session-management/SKILL.md`：`type: dispatcher`，`dispatches_to: opc-session-manager`
- `skills/using-superopc/autonomous-ops/SKILL.md`：`type: dispatcher`，`dispatches_to: opc-cruise-operator`（GREEN/YELLOW/RED 权限规则保留为简要索引，完整语义下沉到 agent + decision_engine + cruise_controller）

### 3. 改所有非只读 slash 命令的 `## 动作` 为"调用 `<skill-id>` skill"
覆盖 7 个会话/巡航命令 + 3 个新增命令（`/opc-debug` `/opc-security` `/opc-business`）。

### 4. Cruise controller 真派发 agent
- `ACTION_AGENT_MAP`：plan/build/review/debug/ship/research/pause/resume → 对应 agent
- `READ_ONLY_SCRIPT_MAP`：health_check/collect_intel/run_tests/format_code/generate_docs → 白名单脚本
- `_run_claude_agent()`：通过 `claude --print --agent <owner>` 真派发，并发 `cruise.agent_dispatch` 事件审计

### 5. 明确只读 CLI 白名单（9 个）
在 `AGENTS.md` §架构契约 新增章节，列明 `/opc-health` `/opc-dashboard` `/opc-stats` `/opc-intel` `/opc-profile` `/opc-backlog` `/opc-seed` `/opc-thread` `/opc-research` 及**进入条件**（完全只读、不触发 agent/skill、输出可直接消费、一旦违反立即改为派发 skill）。

### 6. 机械强制：lint 脚本
`scripts/verify_command_contract.py` 在 CI 中对 `commands/opc/*.md` 做以下检查：
- YAML frontmatter 合法且有 `name`
- 白名单命令可直接调用脚本
- 非白名单命令必须提到 "调用 `<dispatcher-id>` skill"，且不能同时有直接脚本调用

CI `.github/workflows/quality.yml` 的第一步跑此 lint，未通过禁止合并。

## 考虑的替代方案

### 替代方案 A：只修 cruise controller 的假派发
- **优点**：工程量最小
- **缺点**：命令层与 meta skill 的断层继续存在，下次添加命令时又会出现；lint 缺失，靠代码审查兜底
- **淘汰原因**：不系统，无法防止再次发生

### 替代方案 B：把 meta skill 合并进 dispatcher，不新建 agent
- **优点**：少建两个 agent 文件
- **缺点**：违反"skill 不持有 workflow"铁律；四个子场景（pause/resume/progress/report）塞在 skill 里会让 skill 膨胀到 200+ 行，失去"派发器 ≤ 60 行"约束
- **淘汰原因**：违反 v1.4 契约底层设计原则

### 替代方案 C：废弃只读 CLI 命令，全部改为 agent 派发
- **优点**：契约最纯粹，零例外
- **缺点**：`/opc-health` 这样的纯只读诊断派一个 agent 去跑脚本、读输出、再报告——成本远高于直接 `python scripts/opc_health.py`；用户在 CI 里调用会浪费 LLM 调用
- **淘汰原因**：工程成本与契约纯度不成比例

### 替代方案 D：lint 只警告不阻断
- **优点**：摩擦小
- **缺点**：审计已经证明靠人眼巡检必然漏检；警告不阻断等于没有
- **淘汰原因**：恰恰是本次断层能存在这么久的根因

## 后果

### 正面
- **零假派发**：cruise 真的会派发 opc-planner/executor/reviewer，自主模式不再"只刷新面板"
- **命令层契约全覆盖**：25 个命令中 16 个派发 skill，9 个明确白名单
- **机械强制**：lint 接入 CI，任何后续 PR 引入契约违规都会被阻断（已验证：25/25 通过）
- **两个新 agent 填补了会话连续性与自主运营的 workflow 空洞**
- **为后续 agent 新增提供范本**：session-manager/cruise-operator 的"多子场景单 agent"结构可复用到 doc-ops、intel-ops 等类似场景

### 负面
- 命令数量多了 3 个（`/opc-debug` `/opc-security` `/opc-business`）——但它们本就该存在
- lint 增加一个 CI 步骤（~0.2s）
- 白名单是硬编码，扩展白名单需要改 `READ_ONLY_CLI_WHITELIST` + AGENTS.md 双位置——已在 lint hint 里明确提示

### 风险
- **R1**：未来有人新建命令时忘记写 "调用 X skill" 文字 → 缓解：lint 阻断且 hint 给出 dispatcher 列表
- **R2**：白名单被滥用（有人把写命令塞进白名单）→ 缓解：AGENTS.md 白名单条目定义"完全只读"+ 4 条进入规则，PR 审查时可核对
- **R3**：dispatcher skill 的 `dispatches_to` 指向不存在的 agent → 缓解：`build_skill_registry.py --check` 做跨引用校验（已存在）

## 落地清单

| 项 | 文件 | 状态 |
|---|---|---|
| 修 cruise controller 假派发 | `scripts/engine/cruise_controller.py` | ✅ (commit 35e0718) |
| cruise 契约测试 9 个 | `tests/test_engine_v2.py::TestCruiseDispatchContract` | ✅ |
| 新建 opc-session-manager | `agents/opc-session-manager.md` | ✅ (commit 266659b) |
| 新建 opc-cruise-operator | `agents/opc-cruise-operator.md` | ✅ |
| session-management 升级 dispatcher | `skills/using-superopc/session-management/SKILL.md` | ✅ |
| autonomous-ops 升级 dispatcher | `skills/using-superopc/autonomous-ops/SKILL.md` | ✅ |
| 7 个命令改派发 skill | `commands/opc/{pause,resume,progress,session-report,cruise,heartbeat,autonomous}.md` | ✅ (commit cbf27d2) |
| 3 个新命令 | `commands/opc/{debug,security,business}.md` | ✅ (commit 47ecb59) |
| 白名单在 AGENTS.md 明确 | `AGENTS.md` §Read-only CLI 白名单例外 | ✅ |
| lint 脚本 | `scripts/verify_command_contract.py` | ✅ |
| lint 测试 8 个 | `tests/engine/test_verify_command_contract.py` | ✅ |
| CI 接入 | `.github/workflows/quality.yml` | ✅ |

## 决策摘要

| 维度 | 决策 |
|---|---|
| 命令默认行为 | 派发 dispatcher skill（非白名单） |
| 只读白名单 | 硬编码 9 个命令，AGENTS.md + lint 双源同步 |
| Meta skill 被 slash 触发 | 不允许；必须升级为 dispatcher |
| Cruise 真执行动作 | 通过 `claude --agent` 派发，绝不走只读脚本假冒 |
| 强制机制 | `verify_command_contract.py` + CI 阻断 |
| 契约破坏面 | 无（7 个命令的 `## 动作` 段改措辞；脚本调用下沉到 agent 内部） |
