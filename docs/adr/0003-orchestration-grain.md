# ADR-0003: 编排粒度——保持 agent 绑定 + 可选 skill 绑定（双绑定）

**日期**: 2026-04-21
**状态**: proposed
**决策者**: 项目 owner
**关联**: `docs/SKILL-DRIVEN-DESIGN.md` §3.4、`docs/archive/REFACTOR-PLAN.md` §2、`scripts/engine/dag_engine.py`

## 背景

v1.4 契约明确："**agent 是 workflow 的唯一事实源**，skill 是派发器或原子纪律。" `<opc-plan>` XML 里的每个 `<task>` 通过 `file / action / test-expectation` 语义由 `AgentRegistry.route` 打分匹配到一个 agent（`opc-planner.md:57-68`、`dag_engine.py:120-157`）。

参考架构图 4 的编排引擎把 skill 本身视为**可调度的工作流原语**（线性 / 条件 / 并行 / 人工确认）。如果要彻底对齐，`<opc-plan>` 的任务就应当绑定到 **skill**，由 skill 的 `dispatches_to` 再决定 agent。

这一翻转在工程上有两种极端：

- **保守极端**：完全保持 agent 绑定，skill 永远是派发器——等于 ADR-0001 / 0002 的收益只在 Intent Router 层兑现，编排层未受益
- **激进极端**：`<task>` 改为绑定 skill，agent 下沉为 skill 的运行时——**破坏现有全部 `docs/plans/*.md`**，与 v1.4 契约的"agent 是事实源"冲突

需要决定一个**不推倒、可演进、可回退**的中间路径。

## 决策

采用 **"双绑定（Dual-Binding）"** 编排粒度：

1. **默认仍是 agent 绑定**——`<task>` 不显式指定 skill 时，`dag_engine` 走现行 `AgentRegistry.route` 逻辑，100% 向后兼容现有 PLAN.md
2. **新增可选 `<skill>` 字段**——`<task>` 可选地声明 `<skill>X</skill>`，此时：
   - 先从 `skills/registry.json` 取该 skill 的 `dispatches_to` 字段 → 锁定 agent
   - 若 skill 是 atomic/meta（`dispatches_to == null`），则 skill 指令被追加到 prompt，**继续**由 agent router 选择 agent（skill 不改变 agent 选择，只改变 agent 的行为）
3. **v1.4 XML 契约不改动**——现有字段（`file / action / test-expectation / completion-gate / depends_on`）保持原语义，Phase A 只新增 `<skill>`，其他 DSL 扩展（`<conditional>` / `<checkpoint>`）**推迟到路线 C**

该设计让 skill 与 agent 在 task 上**并存**：skill 提供"类别（意图）"，agent 提供"执行者"，编排粒度自然上升到 skill 层而不牺牲 agent workflow 事实源的地位。

## 考虑的替代方案

### 替代方案 A: 保持 agent 绑定（完全保守）

- **优点**: 零 XML 契约改动；零向后兼容风险
- **缺点**: `<opc-plan>` 编排层无法感知 skill，Intent Router 的 skill_id 仅在对话入口被消费，进入 PLAN 后又回到 agent 粒度——架构上**割裂**
- **淘汰原因**: 无法实现参考架构"skill 成为工作流原语"的意图，ADR-0001 的 `dispatches_to` 字段没有运行时消费者

### 替代方案 B: 翻转为 skill 绑定（完全激进）

- **优点**: 完全对齐参考架构图 4 的理想态；语义最统一
- **缺点**:
  - 现有 `docs/plans/2026-04-17-architecture-refactor.md` 与 `docs/plans/2026-04-17-skill-minimization.md` 均为 agent 绑定格式，迁移成本高
  - 与 v1.4 契约"agent 是唯一事实源"冲突，需要同步改 `AGENTS.md`、`CLAUDE.md`、17 份 agent 文件
  - `opc-planner` Phase 2-3 的任务分解模板要重写
  - Atomic skill（tdd / verification-loop）本就是被 agent 调用的，强行翻转会形成"skill 派发给 skill"的循环
- **淘汰原因**: 工程量与破坏面超出路线 A/B 范围；应在路线 C 后再评估

### 替代方案 C: `<task>` 双字段并 required（同时绑定 skill + agent）

- **优点**: 语义最显式
- **缺点**: 信息冗余（agent 可以从 skill 推出）；作者心智负担增加；与"最小改动"原则冲突
- **淘汰原因**: 过度设计

### 替代方案 D: 只在全新 `<opc-plan-v2>` 根标签下启用 skill 绑定

- **优点**: 清晰区分新旧格式
- **缺点**: 解析器要双路径；用户无法在旧 plan 中渐进采纳新能力
- **淘汰原因**: 大版本切换应等到路线 C，Phase A/B 不值得

## 后果

### 正面

- **零破坏**：现有 2 份 PLAN.md 无需迁移
- **渐进采纳**：新 PLAN.md 作者想用 `<skill>` 就加，不想用就不加，选择权在作者
- **skill_id 有运行时消费者**：Intent Router 给出的 skill_id 能在 PLAN.md 中被使用，全链路打通
- **保留升级路径**：当 `<skill>` 字段使用率稳定超过 50% 时，自然可演进到路线 C

### 负面

- `dag_engine.AgentRegistry.route` 需要扩展：优先读 `<skill>` 字段 → 查 skill registry → 回落关键词路由
- `opc-planner` 文档需要一处更新（提示可用 `<skill>`，但不强制）
- 两种绑定并存，新老 PLAN 的阅读需要读者知道两种模式

### 风险

- **风险 R1**：作者过度使用 `<skill>`，把本来由 agent router 智能选择的任务锁死在某 skill 上 → 缓解：`opc-plan-checker` 增加一维检查"显式 skill 是否必要"；文档明确只有"派发器类别"需要显式写
- **风险 R2**：`skill + agent` 组合不合理（如 `<skill>tdd</skill>` + agent 路由到 `opc-doc-writer`）→ 缓解：registry 的 `dispatches_to` 做硬约束；dispatcher 类 skill 显式写 `<skill>` 时强制使用其 `dispatches_to`
- **风险 R3**：双绑定语义让新人困惑 → 缓解：`references/plan-template.md` 增加两种样例，`opc-planner.md` Phase 2 章节明确说明何时用

## 落地入口

- `docs/plans/2026-04-21-skill-driven-runtime-phase-a.md` **不包含** `<skill>` 字段落地（Phase A 只做 Registry + L1 + 观察，不碰 DSL）
- 路线 B 的 PLAN.md 中引入 `<skill>` 字段支持（`dag_engine` 小改 + plan-template 更新 + plan-checker 新维度）
- 路线 C 启动时，本 ADR 可能升级为 `accepted + superseded-by` 指向更大的"skill-primitive 原生 DSL"方案

## 决策摘要

| 维度 | 决策 |
|---|---|
| 默认绑定 | agent（零破坏） |
| 可选绑定 | skill（新增 `<skill>` 字段，Phase B 落地） |
| 契约破坏 | 无（向后兼容） |
| 与 v1.4 冲突 | 无（agent 仍是 workflow 事实源） |
| 升级路径 | 保留到路线 C 再评估 full skill-primitive |
