# ADR-0002: Intent Router 三级递进（L1 规则 / L2 Embedding / L3 LLM）

**日期**: 2026-04-21
**状态**: proposed
**决策者**: 项目 owner
**关联**: `docs/SKILL-DRIVEN-DESIGN.md` §3.2、`scripts/engine/dag_engine.py:120-157`

## 背景

v1.4 下，skill 选择由 LLM 在每次用户请求到来时**读取全部 17 份 `SKILL.md` 的 frontmatter.description** 完成。这相当于参考架构图 2 中的 L3（~500ms、每次都跑），代价高昂且不可审计。

与此同时，agent 侧已有 L1（`AgentRegistry.route` 关键词打分），但两条路由链**彼此独立**，也没有向 L2 embedding 的演进预案。

若要让 skill 成为真正驱动 workflow 的入口，必须引入一个**递进且可退路**的路由层：快路径兜住大多数明确指令，慢路径处理真正模糊的请求。

## 决策

采用**三级递进路由**，路径依次为 **L1 规则/关键词 → L2 Embedding → L3 LLM**，各级独立阈值，命中即返回，降级自然回落。

核心实现要点：

1. **L1：规则 + 关键词精确匹配（~0ms）**
   - 消费 `skills/registry.json` 中每个 skill 的 `triggers.{keywords, phrases, phases}`
   - 打分规则：关键词命中 +10 / phrase 命中 +15 / phase 命中 +5
   - 置信阈值 `L1_CONFIDENT_THRESHOLD = 20`，超阈值直接返回

2. **L2：Embedding 语义检索（~5–20ms，路线 B 启用）**
   - 使用**本地轻量模型**（初步选型 `bge-small-zh` / `bge-small-en-v1.5`，按输入语言分发）
   - skill embedding 离线生成，写入 `skills/embeddings.json`（或对应独立文件）
   - 余弦相似度 top-k=3 作为候选
   - 置信阈值 `L2_CONFIDENT_THRESHOLD = 0.75`，超阈值直接返回

3. **L3：LLM 精确分类（~200–500ms）**
   - 输入仅包含 **L2 top-3 candidates 的 description**（不是全部 17 份）
   - LLM 输出 `{ skill_id, confidence }`
   - 本阶段 token 成本 ≈ 500，远小于原 3200

4. **降级策略**（见 §3.2.3）
   - embedding index 缺失 → L2 跳过，L1 miss 后直接 L3
   - L3 模型不可用 → 返回 L2 top-1 + 低 confidence 警告
   - 三级全 miss → 兜底 `using-superopc` 元技能 + `confidence=0`

5. **可审计日志**：每次路由追加 `.opc/routing/YYYY-MM-DD.jsonl`，字段包括 `input_hash / chosen / path[] / l1_score / l2_top1 / l3_confidence / latency_ms`

阈值采用**保守初始值**，Phase A 上线后由 `learning_store` 聚合真实命中率做离线调优。

## 考虑的替代方案

### 替代方案 1: 只做 L1（关键词路由）

- **优点**: 最简单、0ms、零外部依赖
- **缺点**: 对"帮我想想要不要做这个功能"这类模糊请求无力；命中率会让使用者感到"路由变笨了"
- **淘汰原因**: 退化到比当前 LLM 自由匹配更糟的体验

### 替代方案 2: 只做 L3（让 LLM 每次分类）

- **优点**: 实现简单，直接给 LLM 一份 skill 列表让它选
- **缺点**: 等价于当前体验，没有本质改善；token 成本没降；不可审计
- **淘汰原因**: 零收益

### 替代方案 3: L1 + L3（跳过 L2）

- **优点**: 两级简单；L2 的 embedding 依赖可以省掉
- **缺点**: 对"语义模糊但不包含关键词"的请求体验断崖；L3 负担仍然较重
- **淘汰原因**: 路线 A 本就选择跳过 L2 作为**阶段性**妥协；ADR 固化的是**目标形态**，L2 是未来必须要有的一层

### 替代方案 4: 用云端 embedding 服务（OpenAI embeddings 等）

- **优点**: 质量高、免维护
- **缺点**: 每次路由增加外部请求；隐私合规问题；跨工具（Cursor/Windsurf）运行时未必有统一的 API key
- **淘汰原因**: 违反 `docs/SKILL-DRIVEN-DESIGN.md` §10 D4 决策"本地优先"

## 后果

### 正面

- 大多数明确指令在 L1 完成路由，延迟 0ms、tokens 几乎为 0
- 语义模糊请求由 L2 兜住，LLM 只对真正多意图的请求介入
- 路由日志可被 `learning_store` 和 `/opc-stats` 消费，实现数据驱动的阈值调优
- 三级都有明确降级路径，单点故障不会让系统失能

### 负面

- 新增 `scripts/engine/intent_router.py` 模块和 `.opc/routing/` 日志目录
- 路线 B 引入 embedding 依赖（`sentence-transformers` / `bge-*`）增加安装体积（可选：只在首次路由时按需下载）
- 阈值需要调优窗口期（建议上线后 2 周观察）

### 风险

- **风险 R1**：L1 关键词列表不全导致明确指令漏 L1 命中 → 缓解：把已观察到的历史请求关键词作为初始词表（从 `scripts/hooks/observe.py` 已有观察数据抽取）
- **风险 R2**：中文/英文混合输入 embedding 质量退化 → 缓解：按语言分发到各自模型；建立 benchmark 集
- **风险 R3**：L3 输入不受控（恶意 prompt 注入 candidates）→ 缓解：`candidates` 只从 registry 生成，不允许外部注入；复用 `scripts/hooks/prompt_injection_scan.py`
- **风险 R4**：阈值初始值偏差导致体感倒退 → 缓解：Phase A 上线先做影子模式（shadow mode：路由结果不生效，只记录），对比 LLM 自由匹配的选择差异

## 落地入口

- `docs/plans/2026-04-21-skill-driven-runtime-phase-a.md` 的 **Wave 2 / Task 2.1**（`intent_router.py` L1 + L3）
- `docs/SKILL-DRIVEN-DESIGN.md` §5.1 A3 / §5.2 B1
- L2 embedding 单独在路线 B 的 PLAN.md 中落地（Phase A **不启用 L2**）
