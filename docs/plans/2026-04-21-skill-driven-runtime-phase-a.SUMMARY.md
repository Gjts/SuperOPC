# v1.4.1 Skill-Driven Runtime (Phase A) — 执行摘要

**日期：** 2026-04-21
**PLAN：** [`2026-04-21-skill-driven-runtime-phase-a.md`](./2026-04-21-skill-driven-runtime-phase-a.md)
**状态：** ✅ 完成
**总 commits：** 11（基线 1 + Wave 1-3 共 10 个原子 commit）
**总代码/文档变更：** +3,000 行新增，0 行破坏性删除

## Commit 时间线

| # | Commit | Wave / 任务 | 行数 |
|---|--------|-------------|------|
| 1 | `84f00e1` | W0 — 设计 + 3 ADR + PLAN + ROADMAP 打标 | +1154 |
| 2 | `c60ab41` | W1.1 — `skills/registry.schema.json` | +134 |
| 3 | `851c8c5` | W1.2 — `tests/engine/test_build_skill_registry.py` (RED) | +164 |
| 4 | `6f3f222` | W1.3 — `tests/engine/test_intent_router.py` (RED) | +137 |
| 5 | `6afb0e2` | W1.4 — 17 份 SKILL.md frontmatter 扩展 | +176/-239（含 v1.4.0 残留压缩） |
| 6 | `edee94e` | W2.1 — `scripts/build_skill_registry.py` + registry.json | +840 |
| 7 | `d8b19ad` | W2.2 — `scripts/engine/intent_router.py` | +287 |
| 8 | `533d106` | W3.1 — `scripts/hooks/observe.py` sync | +71 |
| 9 | `b4312b2` | W3.2 — `scripts/opc_quality.py` health check | +62 |
| 10 | `4f1b693` | W3.3 — using-superopc SKILL.md 加速路径段落 | +32 |
| 11 | `1488880` | W3.4 — CHANGELOG + ROADMAP 打标完成 | +84/-14 |

## 测试结果

### 本轮新增 14 个测试 — 100% GREEN

```
tests/engine/test_build_skill_registry.py .......... 8 passed
tests/engine/test_intent_router.py .................. 6 passed
14 passed in 0.24s
```

### 全仓库回归

```
tests/ 总 119 测试：118 passed, 1 failed
```

**唯一 fail：** `tests/test_session_workflow.py::test_convert_all_updates_generated_runtime_metadata_and_commands`

- **根因：** 硬编码 `pluginVersion == "1.0.0"`，实际 `plugin.json.version = 1.4.0`
- **引入时机：** v1.4.0 发版时 plugin.json 升级到 1.4.0，测试未同步
- **与本轮无关：** 已验证 `c10e007`（v1.4.0 基线，v1.4.1 改动前）该测试同样失败
- **建议：** 单独 fix（修测试断言用 glob 匹配或动态读取 plugin.json），不应计入本 task scope

## Pre-flight Gate 回顾

| 维度 | 判决 | 来源 |
|------|------|------|
| plan-check（8 维） | APPROVED | PLAN.md 内 Cascade 代 `opc-plan-checker` |
| assumptions（4 类） | PASS | PLAN.md 内 Cascade 代 `opc-assumptions-analyzer` |
| main 分支例外 | 用户显式授权（C 选项） | 会话 2026-04-21 21:40 |
| pre-existing dirty state | Wave 1.4 commit 内混入 v1.4.0 空行压缩残留 | commit message 显式标注 |

## 兑现 ADR 决策

| ADR | 决策 | 落地状态 |
|-----|------|---------|
| 0001 | 生成式 Registry + frontmatter 扩展可选字段 | ✅ `skills/registry.schema.json` + `scripts/build_skill_registry.py` + `skills/registry.json` |
| 0002 | L1 规则 → L2 embedding → L3 LLM 三级路由 | ✅ Phase A 落地 L1+L3；L2 留 Phase B |
| 0003 | 双绑定（agent 默认 + 可选 skill） | ✅ Registry 中 dispatcher 的 `dispatches_to` 契约 |

## Phase B（v1.4.2）触发条件

- v1.4.1 上线后 2 周观察期结束
- 收集 `.opc/routing/*.jsonl` 的路由命中率数据（L1 命中率 / L3 兜底率）
- 用命中率决定：L2 Embedding 必要性、L1 阈值调优、L3 LLM 供应商选型

## 验证可用性

### 手动烟雾测试

```powershell
# 生成/校验 registry
python scripts/build_skill_registry.py
python scripts/build_skill_registry.py --check   # exit 0 == in sync

# 路由烟雾
python scripts/engine/intent_router.py "帮我规划登录"      # -> planning L1
python scripts/engine/intent_router.py "修一下这个 bug"     # -> debugging L1
python scripts/engine/intent_router.py "xyzzy frobnicate"   # -> using-superopc L3 fallback

# 健康检查
python scripts/opc_health.py health --target repo   # 含 repo.skill-registry-consistency

# 全量 pytest
python -m pytest tests/engine/ -v
```

### 审计日志路径

- `.opc/routing/YYYY-MM-DD.jsonl`（每次路由，含 input_hash）
- `~/.opc/learnings/skill_routing.jsonl`（observe.py 去重归档）

## 后续行动项

1. **修 pre-existing 测试**（不在本 task scope）：
   `tests/test_session_workflow.py:196` 把 `runtime_map["pluginVersion"] == "1.0.0"` 改为读 `plugin.json`。
2. **观察路由数据 2 周**后启动 v1.4.2 (Phase B)。
3. **可选**：在 `.pre-commit-config.yaml` 添加 `build_skill_registry.py --check` 作为 pre-commit hook，
   防止 frontmatter 改动未同步 registry.json。
