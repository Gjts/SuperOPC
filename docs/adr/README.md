# Architecture Decision Records (ADR)

SuperOPC 的架构决策记录。每份 ADR 记录一个**重大、可追溯、影响全局**的架构选择，含背景、考虑的替代方案、最终决策和后果。

格式遵循 `@references/patterns/engineering/adr.md`。

## 索引

| ADR | 标题 | 状态 | 日期 | 关联 |
|-----|------|------|------|------|
| [0001](0001-skill-registry-schema.md) | Skill Registry Schema 与生成策略 | proposed | 2026-04-21 | `docs/SKILL-DRIVEN-DESIGN.md` §3.1 |
| [0002](0002-intent-router-tiers.md) | Intent Router 三级递进（L1 规则 / L2 Embedding / L3 LLM） | proposed | 2026-04-21 | `docs/SKILL-DRIVEN-DESIGN.md` §3.2 |
| [0003](0003-orchestration-grain.md) | 编排粒度：保持 agent 绑定 + 可选 skill 绑定（双绑定） | proposed | 2026-04-21 | `docs/SKILL-DRIVEN-DESIGN.md` §3.4 |

## 生命周期

```
proposed → accepted → [可选] deprecated / superseded
```

- **proposed**：正在讨论中（本批 3 份均处该状态，待评审 §10 D1-D5）
- **accepted**：已落地实施
- **deprecated**：不再适用但保留历史
- **superseded**：被新 ADR 取代（会链接到替代 ADR）

## 决策者与评审

- **决策者**：项目 owner
- **评审触发**：本 README 索引中任一 ADR 由 `proposed → accepted` 前
- **评审方式**：在对应 PLAN.md 的 `## OPC Plan Check` 段落核对 ADR 决策是否已被任务反映
