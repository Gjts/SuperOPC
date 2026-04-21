# Skill-Driven Runtime (Phase B) — 实施计划【草稿】

> **版本目标：** SuperOPC v1.4.2
> **关联设计：** `docs/SKILL-DRIVEN-DESIGN.md` §5.2 路线 B（L2 Embedding + Loader + 仪表板）
> **关联 ADR：** `docs/adr/0002-intent-router-tiers.md` §L2 层待补 · 新增 ADR-0004 (embedding 模型选型) · 新增 ADR-0005 (LLM 供应商选型)
> **前置条件：**
> 1. v1.4.1 Phase A 上线 ≥ 2 周（已于 2026-04-21 完成，观察期结束日 ≈ 2026-05-05）
> 2. 收集到至少 100 条 `.opc/routing/*.jsonl` 真实记录，作为 L1/L3 命中率基线
> 3. 至少一位用户或 CI 在 2 周内至少触发过 20 次 `IntentRouter.route()`
>
> **范围：**
> - ✅ L2 Embedding 检索层（离线索引 + 在线检索 + 阈值调优）
> - ✅ `scripts/engine/skill_loader.py`（运行时 LRU + TTL 缓存）
> - ✅ 真实 LLM 接入替换 Phase A 的 `_call_llm()` mock
> - ✅ `/opc-stats` 仪表板扩展（L1/L2/L3 分布 + cache hit rate）
> - ✅ `scripts/opc_quality.py` 追加 embedding 索引新鲜度检查
> - ❌ **不含**：路线 C 的 skill DSL / agent 下沉为执行引擎（留给 v2.0.0）
>
> **预计耗时：** 8–12h（4 波、原子 commit）
> **入口门控：** 本 PLAN 草稿必须由 `opc-plan-checker` + `opc-assumptions-analyzer` 通过评审，并先决策 4 个决策点（见末尾 §决策清单）才可写 `ready-for-build: true`。
> **状态：** `DRAFT` — 观察期数据采集中，预计 2026-05-05 后解锁。

---

## 开工前必须先做的 4 个决策

| ID | 决策 | 候选 | 默认倾向 |
|---|---|---|---|
| D1 | L2 Embedding 模型 | `bge-small-zh-v1.5`（中文友好, 384 维, 24MB）/ `bge-small-en-v1.5`（英文, 384 维）/ `paraphrase-multilingual-MiniLM-L12-v2`（多语言 384 维） | **默认：bge-small-zh + bge-small-en 双模型按语言分发**（SuperOPC 用户中英混合） |
| D2 | L3 LLM 供应商 | OpenRouter（Claude/GPT-4o/Gemini 统一入口）/ 本地 llama.cpp（gemma-2-2b-it 量化 1.5GB）/ 仅保留 mock | **默认：OpenRouter**（与项目 AI 栈 "OpenRoute 集成 GPT-4/Gemini/Claude" 一致） |
| D3 | Embedding 索引存储 | `skills/embeddings.json`（git 管理, 17×384 浮点 ≈ 100KB）/ `skills/embeddings.npz`（numpy, 更小但二进制）/ `.opc/cache/embeddings.json`（不入仓, 本地重建） | **默认：`skills/embeddings.json`**（小、可审、git-friendly） |
| D4 | Embedding 加载时机 | 模块 import 时 eager / 首次 query 时 lazy / 后台线程预热 | **默认：lazy**（IntentRouter L1 命中时无需加载 embedding, Phase A 观察显示 L1 命中率 ≥ 70%） |

> 每项决策通过后都要写一份轻量 ADR 追加到 `docs/adr/`：ADR-0004 embedding 模型、ADR-0005 L3 供应商、ADR-0006 embedding 存储格式、ADR-0007 embedding 加载策略。

---

<opc-plan>
  <metadata>
    <goal>在 Phase A 的 Registry + L1/L3 基础上补齐 L2 语义检索、运行时 Skill Loader 与路由仪表板，兑现 "Context 成本降至原 15% 以下、路由 p50 延迟 &lt; 50ms、命中率 ≥ 90%" 三大指标</goal>
    <spec-url>docs/SKILL-DRIVEN-DESIGN.md</spec-url>
    <estimated-time>8-12h</estimated-time>
  </metadata>

  <waves>

    <wave id="1" description="契约先行：L2 schema + loader 契约 + 真实 LLM 接口契约 + 仪表板数据模型 (RED)">

      <task id="1.1">
        <title>扩展 skills/registry.schema.json 把 embedding 字段从 null 允许为 array</title>
        <file>skills/registry.schema.json</file>
        <action>把 embedding 字段的 type 从 `["array", "null"]` 保留的基础上，增补子项 items 约束 (type:number, min:-1.0, max:1.0) 和 minItems/maxItems 匹配 embedding 维度常量（384 for bge-small）。新增 top-level `embedding_model` 字段记录索引所用模型名与版本。commit `feat(skills): registry schema 增补 embedding 字段维度约束`</action>
        <test-expectation>Draft7Validator.check_schema 通过；含 384 维向量的样本能通过；含 128 维或非 [-1,1] 的样本被拒</test-expectation>
        <completion-gate>jsonschema check_schema 退出 0；手工构造两个 sample（合法 + 非法维度）分别 validate 成功/失败</completion-gate>
      </task>

      <task id="1.2">
        <title>新建 tests/engine/test_skill_loader.py (RED)</title>
        <file>tests/engine/test_skill_loader.py</file>
        <action>契约：(a) SkillLoader(cache_size=N, ttl_seconds=T) 返回单例级 LRU；(b) .get(skill_id) 命中缓存直接返回；(c) TTL 过期自动重读磁盘；(d) SKILL.md 文件 mtime 变更立即失效；(e) .preload_dependencies(skill_id) 根据 registry.dependencies 预取下游；(f) .stats() 返回 hit_rate / evictions / current_size。所有测试在 skill_loader.py 实现前 RED。commit `test(engine): 添加 skill loader 契约测试 (RED)`</action>
        <test-expectation>pytest tests/engine/test_skill_loader.py 收集到 ≥6 条 failing 测试</test-expectation>
        <completion-gate>文件存在；pytest --collect-only 见 ≥6 条测试</completion-gate>
      </task>

      <task id="1.3">
        <title>扩展 tests/engine/test_intent_router.py 新增 L2 测试 (RED)</title>
        <file>tests/engine/test_intent_router.py</file>
        <action>追加：(a) L1 miss 且 L2 余弦相似度 ≥ L2_CONFIDENT_THRESHOLD (0.75) 时 path == ["L1","L2"]，skill_id 匹配语义同义词场景；(b) L2 miss（相似度 &lt; 0.75）才进 L3；(c) route() 结果新增 `tier_scores.L2`。原有 6 个 L1/L3 测试保持通过。commit `test(router): 添加 L2 embedding 路由契约测试 (RED)`</action>
        <test-expectation>新增 ≥3 条 L2 failing 测试；原 6 条 L1/L3 测试保持绿</test-expectation>
        <completion-gate>pytest tests/engine/test_intent_router.py -k "L2" 至少 3 条 collected 且 failing；-k "not L2" 仍全绿</completion-gate>
      </task>

      <task id="1.4">
        <title>新建 tests/engine/test_router_stats.py (RED)</title>
        <file>tests/engine/test_router_stats.py</file>
        <action>契约 /opc-stats 扩展：(a) read_routing_logs(start_date, end_date) 从 .opc/routing/*.jsonl 聚合返回 `{l1_count, l2_count, l3_count, fallback_count, avg_latency_ms}`；(b) top_skills(n=5) 按路由次数排名；(c) cache_report() 从 skill_loader.stats() 读取 hit_rate。commit `test(stats): 添加路由统计契约测试 (RED)`</action>
        <test-expectation>≥4 条 failing 测试</test-expectation>
        <completion-gate>pytest --collect-only 看到 ≥4 条</completion-gate>
      </task>

    </wave>

    <wave id="2" description="L2 Embedding 实现：离线索引 + 在线检索 + 替换 Phase A mock">

      <task id="2.1" depends_on="1.1">
        <title>新建 scripts/build_skill_embeddings.py（离线索引生成）</title>
        <file>scripts/build_skill_embeddings.py</file>
        <action>按 ADR-0004 决策加载 embedding 模型（默认 bge-small-zh + bge-small-en），为每条 skill 计算 `name + description + triggers.phrases + tags` 拼接后的向量；写 `skills/embeddings.json` 结构 `{model: "bge-small-zh-v1.5", dimension: 384, indexed_at: ISO, vectors: [{id, vector, lang}]}`；支持 `--check` 比对 registry.json 的 skill id 集合与 embeddings.json 的 id 集合，drift 退出非零。commit `feat(skills): 新增 embeddings 离线索引生成器`</action>
        <test-expectation>运行后 skills/embeddings.json 存在且 vectors 长度 == 17；schema 校验通过；--check 对 sync 状态退出 0</test-expectation>
        <completion-gate>生成文件大小 &lt; 200KB；indexed_at 为合法 ISO；每条 vector 模长 ≈ 1.0（已归一化, tolerance ±0.01）</completion-gate>
      </task>

      <task id="2.2" depends_on="1.3,2.1">
        <title>scripts/engine/intent_router.py 追加 L2 层</title>
        <file>scripts/engine/intent_router.py</file>
        <action>
        (1) `__init__` lazy load `skills/embeddings.json` + 根据 ADR-0004 加载 embedding 模型（首次 L2 调用时才加载）；
        (2) `_try_l2(text, lang)` 算 query embedding，与 vectors 做余弦相似度，返回 top-1 + score；
        (3) `route()` 在 L1 miss 后插入 L2 分支：score ≥ L2_CONFIDENT_THRESHOLD (0.75) 命中则 path = ["L1","L2"]；否则继续 L3；
        (4) 记录 tier_scores.L2。
        commit `feat(router): L2 embedding 语义检索层 (Phase A 跳过项补齐)`
        </action>
        <test-expectation>tests/engine/test_intent_router.py 全绿（含 1.3 新增 L2 测试）；手动 route("how do I ship this feature") -&gt; shipping via L2</test-expectation>
        <completion-gate>全部 test_intent_router.py 测试 PASS；.opc/routing/ 日志中 path 含 "L2" 条目至少 1 条（通过测试期间产生）</completion-gate>
      </task>

      <task id="2.3" depends_on="2.2">
        <title>替换 _call_llm 的 mock 为真实 LLM 调用（按 ADR-0005）</title>
        <file>scripts/engine/intent_router.py</file>
        <action>按 ADR-0005 决策（默认 OpenRouter）实现 `_call_llm(prompt, candidates) -> {skill_id, confidence}`：(a) 从 `OPENROUTER_API_KEY` 环境变量读 key（缺失时回退到 Phase A mock 并 log warn）；(b) 固定请求模型 `anthropic/claude-haiku-4.5` 或等价轻量模型；(c) 请求体按 chat completion 格式组装；(d) 超时 5s；(e) 响应失败降级回 mock 不抛；(f) 所有调用写 `.opc/routing/llm_calls.jsonl` 记录 tokens 消耗。commit `feat(router): L3 接入 OpenRouter (保持 mock 降级)`</action>
        <test-expectation>设置 OPENROUTER_API_KEY=fake 时降级 mock，测试通过；不设置环境变量时也降级；集成测试允许用真实 key 但不作为 CI 硬依赖</test-expectation>
        <completion-gate>pytest 全绿（在 mock 模式下）；`.opc/routing/llm_calls.jsonl` 至少记录一条调用</completion-gate>
      </task>

    </wave>

    <wave id="3" description="Skill Loader 实现 + Context Assembler 集成">

      <task id="3.1" depends_on="1.2">
        <title>新建 scripts/engine/skill_loader.py（LRU + TTL + mtime 失效）</title>
        <file>scripts/engine/skill_loader.py</file>
        <action>
        实现 SkillLoader：
        (1) 内部用 `collections.OrderedDict` 实现 LRU；
        (2) 每条缓存项 `{content, loaded_at, mtime}`；
        (3) .get(skill_id) 按 registry.json 解析 path，读 SKILL.md 内容；
        (4) TTL 过期（默认 300s）自动失效；
        (5) 文件 mtime 变化立即失效；
        (6) .preload_dependencies(skill_id) 递归预取 `registry.skills[i].dependencies.downstream / atomic`；
        (7) .stats() 返回 hit_rate / evictions / current_size / total_requests。
        commit `feat(engine): 新增 skill_loader (LRU + TTL + mtime 失效)`
        </action>
        <test-expectation>tests/engine/test_skill_loader.py 全绿；benchmark: 热缓存 1000 次 get 延迟 p99 &lt; 1ms</test-expectation>
        <completion-gate>所有 loader 测试 PASS；`python -c "from scripts.engine.skill_loader import SkillLoader; l=SkillLoader(); l.get('planning'); print(l.stats())"` 输出合理</completion-gate>
      </task>

      <task id="3.2" depends_on="3.1">
        <title>context_assembler.py 集成 SkillLoader 与 phase 级候选集</title>
        <file>scripts/engine/context_assembler.py</file>
        <action>修改 `ContextAssembler`：(a) 内部持有 SkillLoader 单例；(b) `assemble_for_phase(phase)` 根据 PHASE_SKILL_PRIORITY 选候选 skill，通过 loader.get() 读内容；(c) 预算超限时按 priority 降级丢弃低优先级 skill；(d) 暴露 `context_stats()` 返回本次装配的 token 估算。commit `refactor(context): ContextAssembler 使用 SkillLoader 与 phase 候选集`</action>
        <test-expectation>原 tests/test_engine_v2.py::TestContextAssembler 全部绿色；新增 1-2 条测试验证 SkillLoader 被正确调用</test-expectation>
        <completion-gate>tests/test_engine_v2.py 无回归；benchmark: phase=EXECUTING 的 assemble 耗时 p95 &lt; 50ms</completion-gate>
      </task>

    </wave>

    <wave id="4" description="仪表板扩展 + Health 扩展 + 发布封装">

      <task id="4.1" depends_on="1.4,3.1">
        <title>scripts/opc_stats.py 扩展路由/缓存统计</title>
        <file>scripts/opc_stats.py</file>
        <action>新增 `router_stats()` 从 `.opc/routing/*.jsonl` 聚合近 30 天的 L1/L2/L3 分布、avg_latency、top-5 热门 skill；`cache_stats()` 从 SkillLoader.stats() 输出 hit_rate / evictions；CLI 子命令 `opc-stats --router / --cache`。commit `feat(stats): opc-stats 新增路由与缓存统计`</action>
        <test-expectation>tests/engine/test_router_stats.py 全绿；`python scripts/opc_stats.py --router` 输出非空报告</test-expectation>
        <completion-gate>所有 test_router_stats.py PASS；output 含 `L1=%`, `L2=%`, `L3=%`, `cache hit rate=%` 四关键字段</completion-gate>
      </task>

      <task id="4.2" depends_on="2.1">
        <title>scripts/opc_quality.py 追加 embedding 索引新鲜度检查</title>
        <file>scripts/opc_quality.py</file>
        <action>在 validate_repo_checks 尾部 `repo.skill-registry-consistency` 之后新增 `repo.embedding-index-freshness`：比对 skills/embeddings.json 的 `indexed_at` 与 registry.json 的 generated_at；若 embeddings 早于 registry ≥ 1 小时，status=warn（建议 `python scripts/build_skill_embeddings.py`）；缺失 embeddings.json 时 fail。commit `feat(health): 添加 embedding 索引新鲜度检查`</action>
        <test-expectation>`python scripts/opc_health.py health --target repo --json` 输出含 repo.embedding-index-freshness；drift 场景 fail，新鲜场景 pass</test-expectation>
        <completion-gate>新鲜场景 exit 0；人为 touch -t 旧时间 embeddings.json 后 opc-health 报 warn/fail</completion-gate>
      </task>

      <task id="4.3" depends_on="2.1,4.1">
        <title>.gitignore / .gitattributes 配置 + pre-commit hook</title>
        <file>.gitignore, .pre-commit-config.yaml</file>
        <action>(a) 确认 `skills/embeddings.json` 入仓（默认决策 D3）；若最终决策为 .opc/cache 则入 gitignore；(b) 新增 `.pre-commit-config.yaml` 配置 `build_skill_registry.py --check` + `build_skill_embeddings.py --check` 两条 pre-commit 钩子，防止 frontmatter 改动后忘记重新生成。commit `chore(ci): pre-commit 配置 registry + embeddings drift 防线`</action>
        <test-expectation>`pre-commit run --all-files` 在 sync 状态下退出 0；人为改 SKILL.md 后未 rebuild 时退出非零</test-expectation>
        <completion-gate>`.pre-commit-config.yaml` 合法 YAML；本地运行 `pre-commit run` 通过</completion-gate>
      </task>

      <task id="4.4" depends_on="4.1,4.2,4.3">
        <title>CHANGELOG + ROADMAP v1.4.2 打标 + SUMMARY</title>
        <file>CHANGELOG.md, ROADMAP.md, docs/plans/2026-05-05-skill-driven-runtime-phase-b.SUMMARY.md</file>
        <action>把 v1.4.2 条目填写完整（含 ADR-0004/0005/0006/0007 引用、性能指标、迁移说明）；ROADMAP v1.4.2 改 [已完成] 并勾选全部子任务；生成 SUMMARY.md 记录 commit 时间线、测试结果、指标达成情况。commit `docs: v1.4.2 Phase B 收尾 — CHANGELOG + ROADMAP + SUMMARY`</action>
        <test-expectation>全量 pytest 119+ 测试绿（含新增的 skill loader + router stats + L2 router）；ROADMAP 表格 v1.4.2 标记 [已完成]</test-expectation>
        <completion-gate>`git log --oneline Phase-B-start..HEAD` 回忆清晰；SUMMARY 指标表格包含 3 大指标实测值</completion-gate>
      </task>

    </wave>

  </waves>
</opc-plan>

---

## 回滚策略

| Wave | 回滚方式 |
|------|---------|
| Wave 1 全部 | `git revert` 相关 commit；RED 测试是独立文件，删除不影响运行时 |
| Wave 2.1 | 删 `skills/embeddings.json` + revert；无下游依赖 |
| Wave 2.2 | intent_router 回到仅 L1+L3 状态（Phase A 版本），测试回 RED |
| Wave 2.3 | `_call_llm` 回到 mock；`.opc/routing/llm_calls.jsonl` 可保留作审计 |
| Wave 3 | 删 skill_loader.py + revert context_assembler.py 变更；ContextAssembler 回到直接读文件 |
| Wave 4 | 独立 revert 单 commit |

**整体回滚**：Phase B 100% 可回退到 Phase A 状态，运行时 Registry + L1+L3 继续工作。

---

## 性能与验收指标（v1.4.2 上线标准）

| 指标 | 基线（Phase A） | Phase B 目标 | 测量方法 |
|------|----------------|-------------|---------|
| L1 命中率 | 待实测（期望 ≥ 60%） | ≥ 60% | `.opc/routing/*.jsonl` 聚合 |
| L1+L2 合计命中率 | 不适用 | ≥ 85% | 同上 |
| L3 调用率 | 期望 ≥ 40% | ≤ 15% | 同上 |
| Context 成本节省 | 70% | 85% | ContextAssembler token 对比基线 |
| route() p50 延迟 | &lt; 1ms（仅 L1） | &lt; 50ms（含 L2 embedding） | 测试工具 benchmark |
| SkillLoader cache hit rate | 不适用 | ≥ 70% | SkillLoader.stats() |

---

## OPC Plan Check（待填）

> 待 Phase A 观察期结束后由 `opc-plan-checker` 填写。决策 D1-D4 未锁定前此处留空。

## OPC Assumptions Analysis（待填）

> 待 `opc-assumptions-analyzer` 填写。核心假设：
> - **T1**：embedding 模型可离线下载（bge-small 模型在 HuggingFace 公开）
> - **T2**：OpenRouter API key 在 CI/本地均可配置
> - **T3**：embedding 索引规模（17 × 384 floats ≈ 100KB）对 git 仓库可接受
> - **U1**：用户愿意付 L3 LLM 调用费用（估算：月 &lt; $1，按 100 次 L3 × 500 tokens × $0.001/1K 计）
> - **B1**：L2 命中率能把 L3 依赖降至 ≤ 15%（关键经济指标）
> - **O1**：embedding 模型首次加载 &lt; 5s（ONNX Runtime 量化后约 2s）

## OPC Pre-flight Gate

- **plan-check**: `PENDING`（Phase A 观察期未结束）
- **assumptions**: `PENDING`
- **decisions D1-D4**: `PENDING`
- **ready-for-build**: **false**

> 🔒 本 PLAN 为**草稿**，在满足以下所有条件前不得执行：
> 1. Phase A 观察期（≥ 2 周）结束且收集到 ≥ 100 条路由日志
> 2. 决策 D1-D4 锁定并写入 ADR-0004/0005/0006/0007
> 3. `opc-plan-checker` 判决 APPROVED
> 4. `opc-assumptions-analyzer` 判决 PASS
