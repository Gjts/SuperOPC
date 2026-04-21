# SKILL-DRIVEN-DESIGN — Skill 驱动 Agent Workflow 设计提案

> **状态：** 设计草案（draft，不含代码改动）
> **日期：** 2026-04-21
> **作者：** 审查现状 + 对齐 "Skill Registry / Intent Router / Loader / Orchestration Engine" 四组件架构
> **依据：** `docs/REFACTOR-PLAN.md`（v1.3/v1.4 skill-dispatcher 契约已落地）
> **范围：** 仅本文档一份产出。涉及代码的落地动作均在评审结论后另行立项。
> **决策点：** 见文末 §10。

---

## 0. 一页摘要（TL;DR）

当前 SuperOPC 运行在 **v1.4 契约**：`Command → Dispatcher Skill → Agent (workflow 持有者) → Atomic Skill + references/`。
**Agent 是工作流的事实源**；skill 分两种角色——派发器（8 个）与原子纪律（4 个）+ 元层（4 个）+ 学习（1 个）。

对照参考架构的四组件理想态：

| 组件 | 理想态 | 当前状态 | 主要 Gap |
|---|---|---|---|
| ① Skill Registry | 结构化索引（id/tags/embedding/schema/deps/usage） | 仅 frontmatter `name + description` | 🔴 无 registry、无 schema、无 deps、无 stats |
| ② Intent Router | L1 规则 → L2 embedding → L3 LLM 三级递进 | skills 仅 L3（每次 LLM 读 description）；agents 有 L1 | 🟡 缺 skill 级 L1/L2 |
| ③ Skill Loader | LRU+TTL、权限、版本、懒加载 | 仅 `context_assembler.py` phase 静态裁剪 | 🟡 缺运行时缓存/版本 |
| ④ Orchestration Engine | 线性/条件/并行/人工确认 四模式 | `dag_engine` + `cruise_controller` + `decision_engine` 已覆盖 | ✅ 近完备，但编排粒度是 **agent + task**，非 **skill** |

**本提案目标：** 给出让 skill 从"派发器"升级为"工作流原语"的**两条演进路线**——保守与激进——并说明与 v1.4 契约的兼容边界。代码改动不在本文档范围内。

---

## 1. 背景与动机

### 1.1 为什么此时提

- **v1.4 契约已稳定**：`AGENTS.md:1-18` 的四层契约已落地，skill 职责被清洗得很干净（17 个 skill，派发器 8、原子 4、元层 4、学习 1）。这是讨论"skill 如何进一步驱动 agent workflow"的**最佳时间点**——结构清晰，改造面可控。
- **上下文预算压力**：参考架构图 5 给出的量级是 **40 个 skill 全量注入 ≈ 3200 tokens**，按需加载 **≈ 200 + 500–1000 tokens**，节省约 **70%**。SuperOPC 的 `context_assembler.py` 虽已按 phase 做了初级裁剪，但**未把"skill 发现"从 LLM 侧转移到可审计的结构化索引**，仍有较大优化空间。
- **路由可审计性**：目前 skill 选择完全由 LLM 自由匹配 description，**不可复现、不可回放**。引入 registry + 三级路由后，选择过程可解释、可单测、可 A/B。
- **与现有 `agents/registry.json` 对称**：agents 已有 registry，skills 没有。对称化后同一条路由决策链可以横跨 skill 和 agent。

### 1.2 为什么不是"推倒重来"

v1.4 的 skill-dispatcher / agent-workflow 契约解决了**文档冗余与职责漂移**问题。重新把 skill 填回流程详情会复现 v1 的老毛病。**正确做法是保留契约，仅在"发现与加载"层上做结构化增强**。

---

## 2. 现状精确诊断（客观事实）

### 2.1 驱动链路

```
用户自然语言 / slash command
     │
     ▼
`skills/using-superopc/SKILL.md`（元技能：skill-first 门控）
     │
     ▼
Claude 匹配 17 个 SKILL.md 的 frontmatter.description（LLM 自行完成，L3）
     │
     ▼
某个 Dispatcher Skill（e.g. `skills/product/planning/SKILL.md`）
     │
     │ Task() 调用
     ▼
对应 Agent（`agents/opc-planner.md`）—— 持有 Phase 0-5 完整 workflow
     │
     ├── 按需调用 Atomic Skill：tdd / verification-loop / agent-dispatch / git-worktrees
     └── 按需引用 references/（patterns / business / rubric / checklist）
```

### 2.2 已存在的结构化能力

| 能力 | 位置 | 备注 |
|---|---|---|
| Agent Registry | `agents/registry.json` | 含 `capability_tags / scenarios / input / output / priority` |
| Agent Router | `scripts/engine/dag_engine.py:120-157`（`AgentRegistry.route`） | L1 关键词字符串包含打分 + 关键词回退 |
| Phase-aware Skill 优先级 | `scripts/engine/context_assembler.py:66-89` | `PHASE_SKILL_PRIORITY` 按 7 个 phase 给出 skill 列表 |
| DAG 编排引擎 | `scripts/engine/dag_engine.py` | 波次并行 + 重试/降级/升级 + 事件发射 |
| 决策层 | `scripts/engine/decision_engine.py` | 三层：规则 + 状态机 + ICE 启发 |
| 运行模式 | `scripts/engine/cruise_controller.py` | watch / assist / cruise 三模式 + GREEN/YELLOW/RED 分区 |
| 事件总线 | `scripts/engine/event_bus.py` | publish/subscribe；hooks 通过 bridge 汇入 |
| 学习管道 | `scripts/engine/learning_store.py` + `scripts/hooks/observe.py` | PostToolUse 观察 → 模式检测 → 本能演化 |

### 2.3 **缺失** 的结构化能力

| 能力 | 影响 |
|---|---|
| ❌ `skills/registry.json` | skill 发现只能靠 LLM 读 description，每次都 L3 成本 |
| ❌ Skill 的 `input_schema` / `output_schema` | 派发时参数契约靠自然语言描述，无法编程校验 |
| ❌ Skill 的 `dependencies` 声明 | 当前依赖隐含在文档文字里（e.g. "下游走 implementing"） |
| ❌ Skill usage_stats | 无法基于真实使用频率优化 priority / 淘汰低频 |
| ❌ Skill 的版本并存（v1/v2） | 修改 skill 只能单版本替换，无法灰度发布 |
| ❌ Skill 级 DAG 编排 | `<opc-plan>` 的 `<task>` 关联的是 agent，不是 skill |

---

## 3. 设计目标：四组件落地 Schema

### 3.1 组件 ①：Skill Registry

#### 3.1.1 最小可用 Schema（`skills/registry.json`）

```json
{
  "$schema": "SuperOPC Skill Registry v1",
  "version": "2.0.0-draft",
  "description": "Structured index of all skills for Intent Router + Loader.",
  "skills": [
    {
      "id": "planning",
      "name": "Planning Dispatcher",
      "path": "skills/product/planning/SKILL.md",
      "type": "dispatcher",
      "triggers": {
        "keywords": ["规划", "拆解", "怎么实现", "plan", "break down"],
        "phrases": ["帮我规划 X", "X 怎么做"],
        "phases": ["DISCUSSING", "PLANNING"]
      },
      "tags": ["planning", "design", "decomposition", "phase-0-5"],
      "input_schema": {
        "requirement": {"type": "string", "required": true},
        "approved_design_path": {"type": "string", "required": false},
        "spec_path": {"type": "string", "required": false}
      },
      "output_schema": {
        "plan_path": {"type": "string", "pattern": "docs/plans/YYYY-MM-DD-*.md"},
        "ready_for_build": {"type": "boolean"}
      },
      "dispatches_to": "opc-planner",
      "dependencies": {
        "downstream": ["implementing"],
        "atomic": [],
        "references": ["plan-template.md"]
      },
      "version": "1.4.0",
      "deprecated": false,
      "usage_stats": {
        "last_30d_invocations": 0,
        "success_rate": null,
        "avg_tokens_saved": null
      },
      "embedding": null,
      "priority": 90
    }
  ]
}
```

#### 3.1.2 字段语义速查

| 字段 | 语义 | 消费者 |
|---|---|---|
| `id / name / path / type` | 基本身份；`type ∈ {dispatcher, atomic, meta, learning}` | 所有组件 |
| `triggers.{keywords,phrases,phases}` | Intent Router L1 的匹配源 | Intent Router |
| `tags` | 语义标签（embedding 前的粗筛） | Intent Router L2 |
| `input_schema / output_schema` | 接口契约，供 agent 编程校验参数 | Loader / Orchestration |
| `dispatches_to` | dispatcher 指定 Task() 目标 agent；atomic/meta 为 null | Orchestration |
| `dependencies` | 下游 skill / 调用的 atomic / 引用的 reference | Loader（预取） |
| `version / deprecated` | 多版本并存基础 | Loader（灰度）|
| `usage_stats` | 真实使用数据，Post-v0 由 hooks 自动填 | Registry 自我优化 |
| `embedding` | Intent Router L2 向量；Post-v0 离线生成 | Intent Router L2 |
| `priority` | Tie-breaker | Intent Router |

#### 3.1.3 SKILL.md 的 frontmatter 演进（非破坏）

保持现有 `name + description` 不变，**仅新增可选字段**：

```yaml
---
name: planning
description: Use for new features... Dispatches opc-planner.  # 现有，保持
# --- 以下为 v2 可选扩展，允许缺省（兼容 v1.4）---
id: planning                    # 默认 == name
type: dispatcher                # dispatcher | atomic | meta | learning
tags: [planning, design, decomposition]
dispatches_to: opc-planner
version: 1.4.0
---
```

frontmatter 保持可读；**结构化事实源是 `skills/registry.json`**，由脚本从 frontmatter + SKILL.md 聚合生成，避免手维护两处。

---

### 3.2 组件 ②：Intent Router（三级递进）

#### 3.2.1 路由层级

```
用户输入 / 事件
     │
     ▼
┌──── L1: 规则 + 关键词精确匹配（~0ms）─────────────────┐
│ 输入：raw_text                                        │
│ 对每个 skill.triggers.keywords / phrases 做精确匹配    │
│ 命中 ≥ 1：记录 candidates[ ]，score = 匹配次数 × 10    │
│ 覆盖：命令式"规划/ship/修 bug/定价"等明确指令          │
└────┬────────────────────────────────────────────────┘
     │
     │ 若 L1 max(score) ≥ L1_CONFIDENT_THRESHOLD(20)
     │ → 直接出结果（confident hit）
     │
     │ 否则进入 L2
     ▼
┌──── L2: Embedding 语义检索（~5-20ms）────────────────┐
│ 输入：raw_text                                        │
│ 对 raw_text 求 embedding，与 skill.embedding 计算余弦  │
│ 取 top-k（k=3）作为 candidates                        │
│ 覆盖：语义模糊"帮我想想这个功能要不要做"                │
└────┬────────────────────────────────────────────────┘
     │
     │ 若 L2 top1.score ≥ L2_CONFIDENT_THRESHOLD(0.75)
     │ → 直接出结果
     │
     │ 否则 top-3 candidates 进入 L3
     ▼
┌──── L3: LLM 精确分类（~200-500ms）──────────────────┐
│ 输入：raw_text + top-k candidates 的 description      │
│ LLM 从 candidates 中挑一个并给出 confidence           │
│ 覆盖：多意图、需要理解场景的复杂请求                    │
│ 成本：仅 1 次 LLM 调用，input 远小于全量 skill 描述注入  │
└────┬────────────────────────────────────────────────┘
     │
     ▼
输出：{ skill_id, confidence, path[L1/L2/L3], candidates_explored[] }
```

#### 3.2.2 路由记录（可审计）

每次路由结果写入 `.opc/routing/YYYY-MM-DD.jsonl`：

```json
{"ts":"2026-04-21T10:30:00Z","input_hash":"sha1:abc","chosen":"planning","path":["L1"],"l1_score":30,"latency_ms":0.4}
{"ts":"2026-04-21T10:31:00Z","input_hash":"sha1:def","chosen":"business-advisory","path":["L1","L2","L3"],"l1_score":0,"l2_top1":0.61,"l3_confidence":0.87,"latency_ms":340}
```

消费者：
- `learning_store` 聚合观察，检测路由偏差
- 路由质量仪表板（`/opc-stats` 扩展）
- A/B 实验基础设施

#### 3.2.3 降级策略

| 故障 | 降级 |
|---|---|
| embedding index 缺失 / 过期 | L2 跳过，直接 L1 → L3 |
| L3 模型不可用 | 返回 L2 top-1 + 明显低 confidence 警告 |
| 三级全 miss | 兜底返回 `using-superopc` 元技能 + `confidence=0` |

---

### 3.3 组件 ③：Skill Loader

#### 3.3.1 职责

- **加载 SKILL.md 全文**到上下文（Intent Router 返回 id 后）
- **管理缓存**（LRU + TTL）
- **版本选择**（灰度 / 回滚）
- **权限门控**（RED zone skill 需 human approval）
- **依赖预取**（加载 `planning` 时同步预取 `plan-template.md`）

#### 3.3.2 接口草案

```python
# scripts/engine/skill_loader.py (拟新增)
class SkillLoader:
    def __init__(self, registry: SkillRegistry, cache_size: int = 32, ttl_sec: int = 300):
        ...

    def load(self, skill_id: str,
             version: str | None = None,
             zone: str = "GREEN") -> LoadedSkill:
        """
        Returns SKILL.md content + resolved deps.
        Cache key: (skill_id, version, zone).
        """
        ...

    def invalidate(self, skill_id: str | None = None) -> None:
        """File watcher 触发，或版本发布时调用"""
        ...

    def stats(self) -> LoaderStats:
        """cache_hits / misses / evictions / avg_load_ms"""
        ...
```

#### 3.3.3 与 `context_assembler.py` 的关系

| 模块 | 职责 |
|---|---|
| `context_assembler` | **Phase 级批量裁剪**：根据项目 phase 决定哪些 skill / agent / rule 需要"被 Claude 意识到" |
| `skill_loader`（新） | **单 skill 级按需加载**：一次加载一个 skill 的 full body 到对话上下文 |

二者叠加 = 图中 Loader 完整能力。context_assembler 给"候选集"，skill_loader 负责"具体加载"。

#### 3.3.4 缓存策略

- **LRU**：最近使用的 32 个 skill 常驻
- **TTL**：5 分钟未使用的条目过期（文件修改时主动失效）
- **预取**：Intent Router 给出 candidates 后，Top-3 异步预加载
- **跨会话**：`~/.opc/cache/skills/`（可选，v2 再做）

---

### 3.4 组件 ④：Orchestration Engine

#### 3.4.1 现状盘点：**四种模式已有三种**

| 模式 | 实现 | 证据 |
|---|---|---|
| **线性流水线** | `<opc-plan>` XML 的波次顺序 + `opc-orchestrator` | `agents/opc-orchestrator.md:75-98` |
| **并行执行** | `dag_engine._execute_wave` 的 ThreadPoolExecutor | `scripts/engine/dag_engine.py:258-281` |
| **人工确认** | `cruise_controller` YELLOW zone + `autonomous-ops` 权限模型 | `skills/using-superopc/autonomous-ops/SKILL.md:28-50` |
| **条件分支** | ⚠️ 部分：`decision_engine` 支持 if/then，但 `<opc-plan>` XML 无显式语法 | `scripts/engine/decision_engine.py` |

#### 3.4.2 编排粒度的关键选择

**核心问题：** `<opc-plan>` 里的一个 `<task>` 应当绑定到 **agent** 还是 **skill**？

| 选项 | 说明 | 兼容性 | 表达力 |
|---|---|---|---|
| **A. 保持 agent 绑定**（v1.4 现状） | `<task>` 仍指定 `file/action/test-expectation`，由 registry 路由到 agent | ✅ 零破坏 | ⚠️ 工作流原语是 agent 职责单元，不是 skill |
| **B. 双绑定**（推荐路线） | `<task>` 可选 `<skill>X</skill>` 覆盖 agent 路由；未指定时回落 agent 路由 | ✅ 向后兼容 | ✅ skill 可作为原语，但不强制 |
| **C. 翻转为 skill 绑定** | `<task>` 指定 `<skill>`，skill.dispatches_to 决定 agent | 🔴 需迁移全部现有 PLAN.md | ✅ 完全对齐图示理想态 |

**推荐 B**，分阶段接近 C。

#### 3.4.3 条件分支 DSL 草案（v2 XML 扩展）

```xml
<opc-plan>
  <metadata>
    <goal>添加用户登录</goal>
  </metadata>
  <waves>
    <wave id="1" description="后端">
      <task id="1.1">
        <skill>implementing</skill>       <!-- 新增字段，可选 -->
        <title>实现 auth endpoint</title>
        <file>src/api/auth.ts</file>
        <test-expectation>POST /auth returns JWT</test-expectation>
      </task>
    </wave>
    <wave id="2" description="前端+审查" depends-on="1">
      <conditional>                        <!-- 新增：条件分支 -->
        <if test="wave:1:all-passed" />
        <then>
          <task id="2.1">
            <skill>implementing</skill>
            <title>登录表单</title>
          </task>
        </then>
        <else>
          <task id="2.2">
            <skill>debugging</skill>
            <title>修 1.1 失败</title>
          </task>
        </else>
      </conditional>
      <checkpoint human-approval-required="true" zone="YELLOW">
        <!-- 新增：人工确认节点 -->
        <prompt>是否继续部署？</prompt>
      </checkpoint>
    </wave>
  </waves>
</opc-plan>
```

这一 DSL 扩展是**可选路径**，若评审保守，可在 Post-v0 再做。

---

## 4. 与 v1.4 契约的兼容策略

| v1.4 事实 | v2 新增动作 | 是否破坏 |
|---|---|---|
| 8 个 Dispatcher Skill 仍由 LLM 读 description 触发 | 新增 `skills/registry.json` 作为**旁路加速**；LLM 仍可走原路径 | ❌ 不破坏 |
| 4 个 Atomic Skill 由 agent 调用 | registry 记录 `type:atomic`；Loader 支持 agent 显式调用 | ❌ 不破坏 |
| Agent 是 workflow 事实源 | **保持**；skill registry 的 `dispatches_to` 指向 agent | ❌ 不破坏 |
| `<opc-plan>` XML 无 `<skill>` 字段 | v2 允许可选 `<skill>`，缺省时维持现状 | ❌ 向后兼容 |
| `context_assembler` 按 phase 给 skill 优先级 | Loader 消费此优先级做预取 | ❌ 扩展 |
| `hooks/hooks.json` 已有 observe hook | 扩展 `observe.py` 采集 skill 路由数据写 `usage_stats` | ❌ 附加 |
| `agents/registry.json` 现有结构 | skills/registry.json 采用**对称**格式 | ❌ 对称 |

**原则**：v2 = 增强层，不替换层。v1.4 旧流程在 v2 组件缺失时可自然降级回 LLM 匹配。

---

## 5. 两条演进路线

### 5.1 路线 A：轻量路线（≈ 1 天）

**目标：** 补 Skill Registry + L1 路由，立即拿到 Context 节省 + 可审计。

| Step | 产出 | 影响面 |
|---|---|---|
| A1 | `skills/registry.json` 生成脚本 `scripts/build_skill_registry.py` | 新增 1 文件 |
| A2 | 17 个 SKILL.md frontmatter 扩展可选字段 | 17 文件，仅增 |
| A3 | `scripts/engine/intent_router.py` 实现 L1 + L3 fallback（跳过 L2） | 新增 1 文件 |
| A4 | `using-superopc/SKILL.md` 指明"路由优先调 `intent_router.route(text)`" | 1 文件小改 |
| A5 | `scripts/hooks/observe.py` 追加 skill 路由观察 | 1 文件扩展 |
| A6 | `docs/SKILL-DRIVEN-DESIGN.md` 本文档 + CHANGELOG | 已完成本文档 |

**不做：** Embedding（L2）、LRU Loader、版本并存、DSL 条件分支。

**回退：** 路由器出错 → 自然降级回 v1.4 LLM 匹配。

### 5.2 路线 B：中等路线（≈ 3-5 天）

在路线 A 基础上：

| Step | 产出 |
|---|---|
| B1 | 离线 embedding 生成脚本 + L2 路由 |
| B2 | `scripts/engine/skill_loader.py`（LRU + TTL + 依赖预取） |
| B3 | `skills/registry.json.schema.json`（JSON Schema 校验） |
| B4 | `scripts/opc_health.py` 扩展：校验 registry 与 SKILL.md 一致性 |
| B5 | `/opc-stats` 仪表板：路由分布、cache hit rate、usage_stats 可视化 |

### 5.3 路线 C：激进路线（≈ 2 周+）

在路线 B 基础上：

| Step | 产出 |
|---|---|
| C1 | `<opc-plan>` XML 加 `<skill>` / `<conditional>` / `<checkpoint>` DSL |
| C2 | `dag_engine` 支持 skill 粒度编排（`<skill>` 优先于 agent 路由） |
| C3 | skill 多版本并存（`planning@1.4.0` vs `planning@2.0.0`） |
| C4 | 前端 / marketplace 元数据（图中"阶段三：平台化"） |
| C5 | 迁移全部现有 `docs/plans/*.md` 到 skill 粒度 |

---

## 6. 迁移路径 vs 参考架构三阶段

| 参考架构阶段 | SuperOPC 当前 | 路线 A 后 | 路线 B 后 | 路线 C 后 |
|---|---|---|---|---|
| **阶段一 规范化** | 60%（frontmatter 已统一） | 90% | 100% | 100% |
| **阶段二 工具化** | 10%（仅 phase-aware 裁剪） | 40%（Registry + L1） | 85%（+L2+Loader） | 100% |
| **阶段三 平台化** | 0% | 0% | 10%（仪表板） | 60%（版本+DSL） |

---

## 7. 与现有 Engine 层的集成点

```
┌─────────────────────────────────────────────────────────┐
│ 事件层：event_bus.py（现有）                              │
│   +新事件：skill.routed / skill.loaded / skill.invalidated│
└────────┬────────────────────────────────────────────────┘
         │
  ┌──────┴───────┬──────────────┬──────────────┐
  ▼              ▼              ▼              ▼
context_        skill_          intent_        dag_engine
assembler       loader          router         (已有)
(phase 裁剪)    (新增)          (新增)         
   │              │                │              │
   └── 合作：     │                │              └── v2 可选：
       提供候选 ─┘                │                  消费 <skill>
       集给 loader                │                  字段做 skill
                                  │                  粒度编排
                                  │
              ┌───────────────────┴────┐
              │  skills/registry.json  │
              │  (新增事实源)          │
              └────────────────────────┘
                           │
                           │ 由 scripts/build_skill_registry.py
                           │ 从 SKILL.md frontmatter 聚合生成
                           ▼
           17 个 SKILL.md（保持现有；仅 frontmatter 增可选字段）
```

### 7.1 事件契约扩展（路线 A 即可落地）

| 事件 topic | 发射时机 | 负载关键字段 |
|---|---|---|
| `skill.routed` | Intent Router 决策完成 | `skill_id`, `path`, `confidence`, `latency_ms` |
| `skill.loaded` | Loader 首次加载 | `skill_id`, `version`, `tokens`, `cache_hit` |
| `skill.invalidated` | 文件变更触发 | `skill_id`, `reason` |
| `skill.missed` | 三级全 miss | `input_hash`, `fallback` |

消费者：`learning_store` 聚合、`/opc-stats` 展示、`decision_engine` 异常升级。

---

## 8. 风险与假设

### 8.1 风险

| # | 风险 | 可能性 | 缓解 |
|---|---|---|---|
| R1 | LLM 仍倾向读 description 而无视 registry | 中 | 在 `using-superopc/SKILL.md` 明文写"先调 intent_router"；hook 做静默监控 |
| R2 | registry 与 SKILL.md frontmatter 失同步 | 中 | 构建脚本 + `opc_health` 校验 + pre-commit hook |
| R3 | L2 embedding 模型选择影响语义质量 | 中 | 路线 B 做 benchmark；可以用本地轻量模型（如 `bge-small-zh`）|
| R4 | DSL（路线 C）破坏现有 `docs/plans/*.md` | 高 | 仅新写的 plan 用 v2 DSL；旧 plan 保持 v1 兼容 |
| R5 | 路由可审计数据导致隐私问题（路由日志） | 低 | `.opc/routing/` 在 `.gitignore`；`observe.py` 仅哈希输入 |

### 8.2 核心假设

- A1：当前 17 个 skill 的规模是稳定的上限（v1.4 后不会大规模新增）。若新增到 40+，Registry 收益会进一步放大（正好对应图 5 假设）。
- A2：Embedding（L2）对中文 / 英文混合输入可用。需选能处理双语 description 的模型。
- A3：`opc-planner` 的 `<opc-plan>` XML 结构稳定，可安全扩展 `<skill>` 字段。
- A4：用户仍以 Claude Code 为主要宿主；多工具（Cursor/Windsurf 等）的跨工具路由由 `convert.py` 输出时保证。

---

## 9. 不做什么（边界）

- ❌ **不重写 agent workflow**。agent 依旧是事实源，本提案不搬迁任何 workflow 步骤到 skill。
- ❌ **不引入外部 LLM 做 Intent Router L3**（沿用已有模型接口）。
- ❌ **不做 skill marketplace** / 商店 UI —— 那是参考架构"阶段三平台化"，超出本提案。
- ❌ **不改动 `rules/` / `references/`**  —— 知识库下沉已在 v1.4 完成。
- ❌ **不迁移现有已有的 `docs/plans/*.md`**。v2 DSL（若启用）仅对新 plan 生效。

---

## 10. 决策点（评审时需回答）

### 10.1 范围决策

| # | 决策 | 选项 | 建议 |
|---|---|---|---|
| D1 | 选哪条演进路线 | A / B / C | **A → B 分阶段**。先 1 天拿 70% Context 节省，再评估是否推进到 B |
| D2 | 是否启用 `<opc-plan>` 的 `<skill>` 字段 | 是 / 否 | 否（路线 C 再议），避免早期锁死 DSL |
| D3 | `skills/registry.json` 是手维护还是生成 | 手 / 生成 | **生成**（从 frontmatter 聚合），避免双写 |
| D4 | L2 embedding 模型 | 本地轻量 / 云端 | **本地**（避免外部依赖和隐私） |
| D5 | `<checkpoint>` 人工确认是否属于 v1 范围 | 是 / 否 | 否（已由 `cruise_controller` + YELLOW zone 覆盖） |

### 10.2 架构决策（ADR 候选）

若决定推进，需在 `references/patterns/engineering/adr/` 新增 3 份 ADR：

1. **ADR-001-skill-registry-schema** — 固化 `skills/registry.json` 字段
2. **ADR-002-intent-router-tiers** — 固化 L1/L2/L3 阈值与降级规则
3. **ADR-003-orchestration-grain** — 固化"agent 绑定 + 可选 skill 绑定"的双绑定决策

---

## 11. 评审 Checklist

- [ ] 本文档是否与 `docs/REFACTOR-PLAN.md` v2 的三层契约保持一致？
- [ ] 本文档是否**没有**搬运任何 workflow 细节到 skill（保持 agent 为事实源）？
- [ ] 路线 A 的改动清单是否确实控制在 ≈ 6 个文件以内？
- [ ] `skills/registry.json` 字段是否对称于 `agents/registry.json`？
- [ ] Intent Router 的三级阈值（L1=20 / L2=0.75）是否需要实测调优标记？
- [ ] `context_assembler` 与新 `skill_loader` 的职责边界是否清晰？
- [ ] 所有假设（A1-A4）是否已明示？
- [ ] 所有不做的事（§9）是否已明示？
- [ ] 决策点（D1-D5）是否均有**建议默认**可供快速推进？

---

## 12. 下一步

若本文档通过评审：

1. 在 `ROADMAP.md` 新增 **v2.0.0 milestone: "Skill-Driven Runtime"**，并关联路线 A 作为首批工作项
2. 新建 `docs/plans/YYYY-MM-DD-skill-driven-runtime-phase-A.md`（走 `opc-planner` Phase 0-5 标准流程）
3. 创建 3 份 ADR（见 §10.2）
4. 路线 A 各 step 对应的原子任务在 PLAN.md 里波次化

若评审否决 / 要求缩小范围：

- 退路 1：只做 §3.1.3（SKILL.md frontmatter 扩展 + registry 生成脚本），其他组件搁置
- 退路 2：保持现状，将本文档作为**未来复审档案**存档 `docs/archive/`

---

## 附录 A：术语

- **Dispatcher Skill**：`type=dispatcher`；`Task()` 派发给 agent；v1.4 有 8 个
- **Atomic Skill**：`type=atomic`；agent 内部调用的单一纪律；v1.4 有 4 个
- **Meta Skill**：`type=meta`；系统元层规则；v1.4 有 4 个
- **Learning Skill**：`type=learning`；观察与自我进化；v1.4 有 1 个
- **Intent Router**：将用户自然语言请求转为结构化 skill_id 的解析器
- **L1 / L2 / L3**：规则 / Embedding / LLM 三级路由
- **Skill Loader**：按需加载 SKILL.md 并管理缓存的运行时组件
- **Orchestration Engine**：`dag_engine + decision_engine + cruise_controller` 三合一的执行骨架

## 附录 B：引用

- `skills/using-superopc/SKILL.md:36-93` — v1.4 skill 清单
- `AGENTS.md:3-18` — v1.4 契约四层定义
- `CLAUDE.md:103-145` — skill-first 规则 + 17 skill 分类
- `docs/REFACTOR-PLAN.md` — v2 契约完整推导
- `agents/registry.json` — agent 侧 registry（对称样本）
- `scripts/engine/dag_engine.py:120-157` — agent 关键词路由现实现
- `scripts/engine/context_assembler.py:66-89` — phase 级 skill 优先级现实现
- `hooks/hooks.json:120-131` — PostToolUse observe hook 现接入点
