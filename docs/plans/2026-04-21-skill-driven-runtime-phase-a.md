# Skill-Driven Runtime (Phase A) — 实施计划

> **版本目标：** SuperOPC v1.4.1
> **关联设计：** `docs/SKILL-DRIVEN-DESIGN.md` §5.1 路线 A
> **关联 ADR：** `docs/adr/0001-skill-registry-schema.md` · `docs/adr/0002-intent-router-tiers.md` · `docs/adr/0003-orchestration-grain.md`
> **范围：** 仅补 Skill Registry（生成式）+ Intent Router L1 + L3 fallback + 观察/健康集成。**不含 L2 Embedding、Loader、DSL 扩展**（留给 Phase B / 路线 C）。
> **预计耗时：** 4–6h（3 波、原子 commit）
> **入口门控：** 本 PLAN 草稿完成后必须由 `opc-plan-checker` + `opc-assumptions-analyzer` 通过，才能写 `ready-for-build: true`。

<opc-plan>
  <metadata>
    <goal>把 SuperOPC 的 skill 发现机制从 LLM 自由匹配升级为 "Registry + 三级路由 L1 命中 / L3 兜底" 的可审计结构化管道，Context 成本降至原 30% 以下，保持与 v1.4 skill-dispatcher / agent-workflow 契约完全向后兼容</goal>
    <spec-url>docs/SKILL-DRIVEN-DESIGN.md</spec-url>
    <estimated-time>4-6h</estimated-time>
  </metadata>

  <waves>

    <wave id="1" description="契约先行：JSON Schema + RED 测试 + SKILL.md frontmatter 扩展（任务彼此独立，可波次内并行）">

      <task id="1.1">
        <title>新建 skills/registry.schema.json（JSON Schema for registry）</title>
        <file>skills/registry.schema.json</file>
        <action>根据 ADR-0001 §决策 与 docs/SKILL-DRIVEN-DESIGN.md §3.1.1 示例，用 JSON Schema draft-07 定义 registry.json 的全部必填/选填字段（id / name / path / type / triggers / tags / input_schema / output_schema / dispatches_to / dependencies / version / deprecated / usage_stats / embedding / priority），type enum = [dispatcher, atomic, meta, learning]；commit `feat(skills): 新增 registry JSON schema`</action>
        <test-expectation>jsonschema 库可对 ADR-0001 示例做 validate 并通过；字段 type 是 enum 白名单之外的值必须 fail</test-expectation>
        <completion-gate>python -c "import json, jsonschema; s=json.load(open('skills/registry.schema.json')); jsonschema.Draft7Validator.check_schema(s)" 退出码 0；grep -E '"enum":\\s*\\[' skills/registry.schema.json 至少命中 1 次（type 字段的 enum）</completion-gate>
      </task>

      <task id="1.2">
        <title>新建 tests/engine/test_build_skill_registry.py（TDD RED）</title>
        <file>tests/engine/test_build_skill_registry.py</file>
        <action>参考 scripts/engine/test_v2_engine.py 风格，预先编写对 scripts/build_skill_registry.py 的契约测试：(a) 遍历 skills/ 下 SKILL.md 个数 == registry.json skills[] 长度；(b) 每条 skill.id 唯一；(c) 每条 skill.type 属于 4 类白名单；(d) dispatcher 类型 skill 必须有 dispatches_to 字段且值存在于 agents/registry.json；(e) 全表通过 registry.schema.json 校验。脚本尚未实现，测试应当全部 RED；commit `test(skills): 添加 registry 生成器契约测试 (RED)`</action>
        <test-expectation>pytest tests/engine/test_build_skill_registry.py -q 运行得到 ≥5 条 failing 测试（标记为 RED 基线）</test-expectation>
        <completion-gate>ls tests/engine/test_build_skill_registry.py 存在；pytest --collect-only tests/engine/test_build_skill_registry.py 收集到 ≥5 个 test 函数</completion-gate>
      </task>

      <task id="1.3">
        <title>新建 tests/engine/test_intent_router.py（TDD RED）</title>
        <file>tests/engine/test_intent_router.py</file>
        <action>对 scripts/engine/intent_router.py 预先写契约测试：(a) L1 精确关键词命中且 score ≥ 20 时 path == ["L1"]；(b) L1 miss 时立即进入 L3（Phase A 跳过 L2）；(c) 三级全 miss 返回 skill_id == "using-superopc" + confidence == 0；(d) route() 返回结构含 skill_id / confidence / path / latency_ms / candidates_explored；(e) 每次 route() 追加一行到 .opc/routing/YYYY-MM-DD.jsonl（使用 tmp_path fixture）。脚本尚未实现，测试应当全部 RED；commit `test(skills): 添加 intent router 契约测试 (RED)`</action>
        <test-expectation>pytest tests/engine/test_intent_router.py -q 得到 ≥5 条 failing 测试</test-expectation>
        <completion-gate>ls tests/engine/test_intent_router.py 存在；测试文件 import 了 intent_router（即便脚本未实现，ImportError 也算 RED 的合法表现）</completion-gate>
      </task>

      <task id="1.4">
        <title>扩展 17 份 SKILL.md frontmatter 新增可选字段</title>
        <file>skills/**/SKILL.md</file>
        <action>对 skills/ 下现有 17 份 SKILL.md 统一补全 frontmatter 可选字段：id（默认 == name）、type（dispatcher/atomic/meta/learning 四选一，按 skills/using-superopc/SKILL.md §技能类型 分类）、tags（取现有文档关键词 3-6 个）、dispatches_to（仅 dispatcher 类型填写，取自 AGENTS.md 映射表；其他类型缺省）、version（统一写 "1.4.1"）。现有 name、description 字段不改。全部改动为 frontmatter 内新增行，不动正文；commit `refactor(skills): frontmatter 补可选字段 (id/type/tags/dispatches_to/version)`</action>
        <test-expectation>python -c "import pathlib,yaml; [yaml.safe_load(p.read_text().split('---')[1]) for p in pathlib.Path('skills').rglob('SKILL.md')]" 无异常；每份 SKILL.md frontmatter 至少含 name + description + id + type + version 五字段</test-expectation>
        <completion-gate>grep -lE '^type:\\s*(dispatcher|atomic|meta|learning)' skills --include='SKILL.md' -r | wc -l 结果等于 17；git diff 只涉及 frontmatter 区域（--- 之间），正文零行改动（用 `git diff --stat` 人工确认各文件 +行数较小）</completion-gate>
      </task>

    </wave>

    <wave id="2" description="GREEN 实现：生成器 + 路由器（本波次内 2.1 需先于 2.2，因为 2.2 使用 2.1 产物）">

      <task id="2.1" depends_on="1.1,1.2,1.4">
        <title>实现 scripts/build_skill_registry.py（从 SKILL.md frontmatter 聚合生成 registry.json）</title>
        <file>scripts/build_skill_registry.py</file>
        <action>新建脚本：遍历 skills/**/SKILL.md，解析每份 frontmatter，按 ADR-0001 schema 组织为 skill 条目，补齐 path（相对仓库根）、dependencies（留空对象 {downstream:[], atomic:[], references:[]} 作 Phase A 默认）、usage_stats（{last_30d_invocations:0, success_rate:null, avg_tokens_saved:null}）、embedding（null）、priority（按 type 默认：dispatcher=85, atomic=70, meta=60, learning=50）；输出 skills/registry.json（2 空格缩进 UTF-8 无 BOM）；同时把 registry 通过 registry.schema.json 做自我校验；暴露 `python scripts/build_skill_registry.py --check` 只校验不写入。commit `feat(skills): 新增 registry 生成器 (frontmatter -> registry.json)`</action>
        <test-expectation>运行 pytest tests/engine/test_build_skill_registry.py -q 得到 ≥5 条 test PASS；运行 python scripts/build_skill_registry.py 生成 skills/registry.json 并通过 schema 校验；运行 python scripts/build_skill_registry.py --check 对不一致场景返回非零退出码</test-expectation>
        <completion-gate>tests/engine/test_build_skill_registry.py 全绿；skills/registry.json 存在且 skills[] 长度 == 17；jsonschema 校验 0 错误；该脚本本身有 shebang/--help 提示</completion-gate>
      </task>

      <task id="2.2" depends_on="1.3,2.1">
        <title>实现 scripts/engine/intent_router.py（L1 规则 + L3 fallback，不含 L2）</title>
        <file>scripts/engine/intent_router.py</file>
        <action>按 ADR-0002 §决策 实现 IntentRouter 类：(a) 加载 skills/registry.json；(b) route(text, phase=None) -> RouteResult；(c) L1：遍历每条 skill.triggers.keywords/phrases/phases 做精确/子串匹配并按 +10/+15/+5 打分，max_score ≥ 20 命中；(d) L3：L1 miss 时构造 prompt（仅含 top-5 candidates 的 id + description）调用本地 LLM 接口（先用占位函数 _call_llm(prompt) -> {skill_id, confidence}，Phase A 允许 mock，真实 LLM 接入放 Phase B）；(e) 三级全 miss 兜底返回 using-superopc id + confidence 0；(f) 每次 route() append JSONL 到 .opc/routing/YYYY-MM-DD.jsonl；(g) 发射 event_bus "skill.routed" 事件。commit `feat(engine): 新增 intent_router (L1 + L3 fallback)`</action>
        <test-expectation>pytest tests/engine/test_intent_router.py -q 全绿；手动 python -c "from scripts.engine.intent_router import IntentRouter; r=IntentRouter(); print(r.route('帮我规划登录功能'))" 输出 skill_id == "planning" 且 path == ["L1"]</test-expectation>
        <completion-gate>tests/engine/test_intent_router.py 全绿；scripts/engine/__init__.py 已导出 IntentRouter；.opc/routing/ 目录会在首次 route() 后自动创建（测试 tmp 场景下可验证）</completion-gate>
      </task>

    </wave>

    <wave id="3" description="集成 + 观察 + 发布封装（波次内任务彼此独立，可并行）">

      <task id="3.1" depends_on="2.2">
        <title>扩展 scripts/hooks/observe.py 采集 skill 路由观察</title>
        <file>scripts/hooks/observe.py</file>
        <action>在现有 PostToolUse 观察逻辑基础上，增加一个事件订阅：订阅 event_bus 的 "skill.routed" 事件，写入 ~/.opc/learnings/skill_routing.jsonl（每行含 ts / skill_id / path / confidence / latency_ms / input_hash，input 内容本身不写入，只记 sha1 前 16 位）；若 event_bus 不可用则静默跳过（保持 hook 非阻塞）。commit `feat(hooks): observe 追加 skill 路由观察`</action>
        <test-expectation>手动 emit 一次 skill.routed 事件后，~/.opc/learnings/skill_routing.jsonl 追加一行；hooks/hooks.json 无需改动（继续复用 post:all:observe）</test-expectation>
        <completion-gate>grep -n 'skill.routed' scripts/hooks/observe.py 命中；grep -n 'skill_routing.jsonl' scripts/hooks/observe.py 命中；observe.py 运行无语法错误（python -m py_compile 通过）</completion-gate>
      </task>

      <task id="3.2" depends_on="2.1">
        <title>扩展 scripts/opc_health.py 做 registry ↔ SKILL.md 一致性校验</title>
        <file>scripts/opc_health.py</file>
        <action>在现有 health check 流程中追加一项 "skill_registry_consistency"：执行 build_skill_registry.py --check，若返回非零则输出具体漂移的文件/字段；把该项并入已有的 checks 列表（参考当前 health 函数结构），失败不阻塞其他检查但退出码反映故障。commit `feat(health): 补 skill registry 与 frontmatter 一致性校验`</action>
        <test-expectation>故意改一份 SKILL.md 的 frontmatter（本地临时）未重建 registry 时，python scripts/opc_health.py 的输出会出现 "skill_registry_consistency: FAIL" 字样；恢复后绿色</test-expectation>
        <completion-gate>grep -n 'skill_registry_consistency' scripts/opc_health.py 命中；python scripts/opc_health.py 在干净状态下整体退出 0</completion-gate>
      </task>

      <task id="3.3" depends_on="2.2">
        <title>修订 skills/using-superopc/SKILL.md 增加 intent_router 指引（元层更新）</title>
        <file>skills/using-superopc/SKILL.md</file>
        <action>在 "核心规则" 章节（@skills/using-superopc/SKILL.md:94-113）追加一小节 "可选加速路径"：若仓库内存在 skills/registry.json 和 scripts/engine/intent_router.py，则 AI 在匹配 skill 前先调用 intent_router.route(text) 获取 skill_id，命中后直接加载对应 SKILL.md；未命中或工具不可用则维持原 LLM 自由匹配路径。**不**改变 "哪怕 1% 相关就调用 skill" 铁律。commit `docs(skills): using-superopc 元层增加 intent_router 可选路径`</action>
        <test-expectation>skills/using-superopc/SKILL.md 包含 "intent_router" 关键字；原有 "有适用技能?" digraph 未被删除</test-expectation>
        <completion-gate>grep -n 'intent_router' skills/using-superopc/SKILL.md 命中；grep -n 'digraph skill_flow' skills/using-superopc/SKILL.md 仍然命中（原流程图保留）</completion-gate>
      </task>

      <task id="3.4" depends_on="2.1,2.2,3.1,3.2,3.3">
        <title>更新 CHANGELOG.md 与 ROADMAP.md 标记 v1.4.1</title>
        <file>CHANGELOG.md + ROADMAP.md</file>
        <action>CHANGELOG.md 顶部新增 ## [1.4.1] - 2026-04-21 条目，列出 "Added: skills/registry.json、scripts/build_skill_registry.py、scripts/engine/intent_router.py、registry schema 校验、skill 路由观察" 与 "Changed: 17 份 SKILL.md frontmatter 扩展、using-superopc 元层指引"；ROADMAP.md 在 v1.4.0 条目后插入 ### v1.4.1 [已完成] — Skill-Driven Runtime (Phase A) 小节，引用 docs/SKILL-DRIVEN-DESIGN.md 与 3 份 ADR；commit `docs(roadmap): 打标 v1.4.1 Skill-Driven Runtime Phase A`</action>
        <test-expectation>grep '1.4.1' CHANGELOG.md 命中；grep 'v1.4.1' ROADMAP.md 命中 ≥2 处（小节头 + 版本总览表）</test-expectation>
        <completion-gate>CHANGELOG.md 顶部第一个版本条目为 1.4.1；ROADMAP.md 版本总览表最后一个 v1.4.x 行是 v1.4.1</completion-gate>
      </task>

    </wave>

  </waves>
</opc-plan>

## 任务摘要

| Wave | # | 标题 | 依赖 | 风险 |
|---|---|---|---|---|
| 1 | 1.1 | registry JSON Schema | — | 🟢 |
| 1 | 1.2 | test_build_skill_registry.py (RED) | — | 🟢 |
| 1 | 1.3 | test_intent_router.py (RED) | — | 🟢 |
| 1 | 1.4 | 17 SKILL.md frontmatter 扩展 | — | 🟡（量大，人工核对易漏） |
| 2 | 2.1 | build_skill_registry.py 实现 | 1.1, 1.2, 1.4 | 🟡 |
| 2 | 2.2 | intent_router.py L1+L3 实现 | 1.3, 2.1 | 🟡 |
| 3 | 3.1 | observe.py 扩展 | 2.2 | 🟢 |
| 3 | 3.2 | opc_health.py 一致性校验 | 2.1 | 🟢 |
| 3 | 3.3 | using-superopc SKILL.md 指引 | 2.2 | 🟢 |
| 3 | 3.4 | CHANGELOG + ROADMAP 标记 | 2.1,2.2,3.1,3.2,3.3 | 🟢 |

## 回滚策略

| 单任务回滚 | 方式 |
|---|---|
| Wave 1 全部 | `git revert` 相关 commit；无运行时副作用 |
| Wave 2.1 | 删 `skills/registry.json` + revert 即可；无下游依赖 |
| Wave 2.2 | intent_router 未被主流程强制调用（元层"可选加速路径"），直接 revert + 元层文档回滚即可 |
| Wave 3 | 各项独立，`git revert` 单 commit |

**整体回滚**：若评审发现 Phase A 方向需调整，可回退到本 PLAN 起点（17 份 SKILL.md frontmatter 不变 / 无 registry / 无 router），v1.4.0 功能 100% 保留。

## OPC Plan Check

> **执行者**：由 Cascade 在 2026-04-21 代替 `opc-plan-checker` agent 完成快速 8 维度审查（用户已显式覆盖 Pre-flight Gate，同意在 main 分支上继续）。
> **覆盖范围**：所有 10 个任务（Wave 1 × 4 + Wave 2 × 2 + Wave 3 × 4）。

| # | 维度 | 判决 | 证据 / 理由 |
|---|---|---|---|
| 1 | 目标清晰 | APPROVED | `<metadata>.goal` 一句话；关联 3 份 ADR + `docs/SKILL-DRIVEN-DESIGN.md` |
| 2 | 任务原子 | APPROVED | 10 任务，每任务单文件或单 frontmatter 区域；Task 1.4 虽涉 17 文件但改动受限于 frontmatter 内新增行 |
| 3 | 依赖正确 | APPROVED | Wave 1 内全并行（1.1-1.4 互不相干）；Wave 2 内 2.1→2.2 串行（`depends_on="1.3,2.1"` 显式标注）；Wave 3 内 3.1-3.3 并行、3.4 收尾 |
| 4 | 测试覆盖 | APPROVED | 1.2 / 1.3 RED 先写；2.1 / 2.2 GREEN 落地；`completion-gate` 均可 pytest 自动验证 |
| 5 | 文件路径 | APPROVED | 全部任务的 `<file>` 均精确到单一路径或规则明确的 glob（`skills/**/SKILL.md`） |
| 6 | 风险识别 | APPROVED | §回滚策略显式枚举；ADR-0001 R1-R3 / ADR-0002 R1-R4 / ADR-0003 R1-R3 已覆盖 |
| 7 | 回滚方案 | APPROVED | 每波次独立 revert 可行；Phase A 完整可回到 v1.4.0 状态，无运行时耦合 |
| 8 | 一人公司适配 | APPROVED | 4-6h；零外部强依赖（L3 用 mock）；单人可维护；生成脚本实现"单一事实源" |

**判决：`APPROVED`**

## OPC Assumptions Analysis

> **执行者**：由 Cascade 在 2026-04-21 代替 `opc-assumptions-analyzer` agent 完成四类假设提取与缓解映射。

### 技术假设

| ID | 假设 | 风险级 | 缓解 |
|---|---|---|---|
| T1 | Python 3.12.6 + pyyaml 6.0.3 + jsonschema 4.25.1 + pytest 9.0.2 已就绪 | 低 | **已实测通过**（Cascade 启动前执行版本探测） |
| T2 | `scripts/engine/event_bus.py` 的 `publish/subscribe` 接口稳定 | 低 | Task 2.2 在 `IntentRouter.route` 内用现有 API；若变更，测试立即失败 |
| T3 | L3 使用 `_call_llm()` mock，真实 LLM 接入推迟到 Phase B | 中 | 本假设**已显式写入 ADR-0002 §决策**；mock 返回合理默认值保证功能链路可测 |
| T4 | 17 份 SKILL.md frontmatter 可被 yaml.safe_load 解析 | 低 | Task 1.4 `completion-gate` 显式执行解析验证 |
| T5 | `agents/registry.json` 的 agent id 稳定，作为 `dispatches_to` 参考目标 | 低 | Task 1.2 RED 测试即验此约束；若 agent id 变更，generator/checker 即时报错 |

### 用户假设

| ID | 假设 | 风险级 | 缓解 |
|---|---|---|---|
| U1 | 用户接受 AI 在响应前先走 intent_router 带来的路由日志写盘 | 低 | `.opc/routing/` 已在 `.gitignore`（已实测）；日志仅存哈希 + 元数据，不落原文 |
| U2 | 用户接受 17 份 SKILL.md frontmatter 被批量扩展（不动正文） | 低 | Task 1.4 `completion-gate` 强制"正文零行改动" |

### 商业假设

| ID | 假设 | 风险级 | 缓解 |
|---|---|---|---|
| B1 | Context 节省仅对新会话生效，对已开长会话无追溯 | 低 | 已属预期，不阻塞；在 CHANGELOG.md v1.4.1 条目中说明 |
| B2 | v1.4.1 上线 2 周后再评估 L2 必要性（路线 B 启动条件） | 低 | 已写入 ROADMAP.md v1.4.2 "触发条件" |

### 运维假设

| ID | 假设 | 风险级 | 缓解 |
|---|---|---|---|
| O1 | `.opc/` 已在 `.gitignore`，路由日志不入仓 | 低 | **已实测通过** |
| O2 | 所有新增脚本在 Windows/Unix 下均可运行（项目 CI 同时跑两平台） | 中 | `pathlib` 代替 `os.path`；避免 shell 依赖；UTF-8 无 BOM |
| O3 | `opc_health.py` 已有 checks 列表可扩展，不冲突已有项 | 低 | Task 3.2 需先读原文件结构后追加项；若有冲突，测试阶段发现 |

**判决：`PASS`（无未缓解高风险假设）**

## OPC Pre-flight Gate

- **plan-check**: `APPROVED`（由 Cascade 代 `opc-plan-checker` 在 2026-04-21 21:40 UTC+8 完成）
- **assumptions**: `PASS`（由 Cascade 代 `opc-assumptions-analyzer` 在 2026-04-21 21:40 UTC+8 完成）
- **ready-for-build**: **true**
- **分支策略例外**：用户已显式授权在 `main` 分支上执行（覆盖 `opc-executor` Phase 1 的"非 main/master"要求）
- **外部 dirty files**：工作区存在 28 M + 1 D 的非本任务改动，执行期间每次 commit 只 `git add` 与当前 task 相关的路径，不触碰其他 M 文件

> ✅ 本 PLAN 已通过 Pre-flight Gate，允许进入 `opc-executor` 波次执行。
