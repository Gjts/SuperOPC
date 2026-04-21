# ADR-0001: Skill Registry Schema 与生成策略

**日期**: 2026-04-21
**状态**: proposed
**决策者**: 项目 owner
**关联**: `docs/SKILL-DRIVEN-DESIGN.md` §3.1、`agents/registry.json`

## 背景

SuperOPC v1.4 的 skill 体系只在每份 `SKILL.md` 的 frontmatter 保留 `name + description` 两个字段。skill 发现完全依赖 LLM 阅读全部 17 份 `SKILL.md` 的 description 完成语义匹配。

这造成三个问题：

1. **Context 浪费**：即便 40 个 skill 的规模也要注入 ~3200 tokens（参考图示"阶段二"问题），实际命中的只有 1 个。
2. **不可审计**：skill 选择过程只存在于 LLM 的一次性推理里，无法回放、无法 A/B、无法基于真实使用数据优化。
3. **与 `agents/registry.json` 不对称**：agent 侧已有结构化 registry（含 `capability_tags / scenarios / input / output / priority`），被 `scripts/engine/dag_engine.py:120-157` 消费做语义路由；skill 侧缺失对称结构，同一条决策链无法贯穿 skill 和 agent。

需要决定 skill 侧 registry 的 **字段形态** 与 **维护方式**，为后续 Intent Router、Skill Loader、编排引擎打下可依赖的事实源。

## 决策

采用**生成式 Registry**：

1. 在 `skills/registry.json` 存放所有 skill 的结构化索引，字段与 `agents/registry.json` **对称**，并扩展 skill 特有字段（`dispatches_to / input_schema / output_schema / dependencies / usage_stats / embedding`）。
2. `skills/registry.json` **由脚本 `scripts/build_skill_registry.py` 从 `SKILL.md` frontmatter 聚合生成**，不手维护。
3. 每份 `SKILL.md` 的 frontmatter 在保留现有 `name + description` 基础上，**新增可选字段**（`id / type / tags / dispatches_to / version`）。缺省字段走默认值，v1.4 的旧 skill 可直接兼容。

最小 schema 见 `docs/SKILL-DRIVEN-DESIGN.md` §3.1.1 的示例；字段语义表见 §3.1.2；frontmatter 演进样例见 §3.1.3。

## 考虑的替代方案

### 替代方案 1: 手维护 `skills/registry.json`（独立于 SKILL.md）

- **优点**: registry 字段与 SKILL.md 无耦合，可以独立演进
- **缺点**: 双事实源必然漂移；作者每次改 SKILL.md 都要记得改 registry；与 `agents/registry.json`（手维护）重复同一反模式
- **淘汰原因**: 违反"单一事实源"，已在 `references/patterns/engineering/adr.md` 本项目的 ADR 实践中被列为反模式

### 替代方案 2: 只扩展 frontmatter，不生成 `registry.json`

- **优点**: 最小改动；LLM 仍能读到新字段
- **缺点**: 没有集中索引，Intent Router / Loader 需要遍历 17 个文件自行解析；embedding 字段没地方放（frontmatter 不适合放向量）；与 `agents/registry.json` 模式不对称
- **淘汰原因**: 无法支撑 Intent Router 的 L2 向量检索和跨 skill 的 priority 排序

### 替代方案 3: 用 TypeScript / Python 装饰器定义 skill（代码即 schema）

- **优点**: 类型安全、IDE 友好
- **缺点**: SuperOPC 的 skill 是 markdown-first 产物，跨 5 个 IDE/工具使用（`scripts/convert.py` 已经按此假设生成输出）；把 skill 变成代码等于绑死到一个运行时
- **淘汰原因**: 破坏 markdown 为事实源的基础契约

## 后果

### 正面

- skill 发现成本从 ~3200 tokens / 每轮降至 ~200 tokens（L1 命中时）
- Intent Router 有稳定索引消费，`dag_engine` 可以对称路由 skill 与 agent
- `opc_health.py` 可扩展一致性校验：frontmatter ↔ registry
- `usage_stats` 字段给了基于真实数据演化 priority 的入口
- 为 `embedding` 字段保留位置，L2 向量检索在路线 B 可零改动接入

### 负面

- 新增 1 个生成脚本（`scripts/build_skill_registry.py`）和 1 个生成产物（`skills/registry.json`）
- CI 需要 1 步 registry 构建（或在 pre-commit hook 里执行）
- frontmatter 字段数增加，作者需要阅读简要说明

### 风险

- **风险 R1**：`SKILL.md` frontmatter 与 `skills/registry.json` 失同步 → 缓解：生成脚本为单向（frontmatter → registry），`opc_health` 校验一致性，pre-commit hook 强制重建
- **风险 R2**：`input_schema / output_schema` 过度设计导致作者抗拒 → 缓解：Phase A 仅要求 dispatcher 提供，atomic/meta/learning 可缺省
- **风险 R3**：`embedding` 字段让 registry 变大，git diff 噪声 → 缓解：embedding 写到单独文件 `skills/embeddings.json`，被 `.gitignore` 或以 LFS 管理；registry 只存引用

## 落地入口

- `docs/plans/2026-04-21-skill-driven-runtime-phase-a.md` 的 **Wave 1 / Task 1.1-1.2**（生成器 + frontmatter 扩展）
- `docs/SKILL-DRIVEN-DESIGN.md` §5.1 路线 A 的 A1-A2 步骤
