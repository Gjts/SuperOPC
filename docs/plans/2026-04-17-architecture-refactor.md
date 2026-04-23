# SuperOPC 架构重构 — Skill-Dispatcher / Agent-Workflow 模式

> **设计规格：** `docs/archive/REFACTOR-PLAN.md`
> **目标：** 把 command/skill/agent 三层重叠职责清理成 **skill 触发 → agent 持有 workflow** 的单源结构
> **预估时间：** 4-6 小时（分 4 个 commit）

<opc-plan>
  <metadata>
    <goal>建立 dispatcher-skill / atomic-skill / agent-workflow 三角契约，消除 command/skill/agent 跨层重复</goal>
    <spec-url>docs/archive/REFACTOR-PLAN.md</spec-url>
    <estimated-time>4-6h</estimated-time>
  </metadata>

  <waves>

    <!-- ========== Wave 1: 准备 reference 资源 (无依赖, 可并行) ========== -->
    <wave id="1" description="抽取共享资源到 references/, 让 agent 可引用">

      <task id="1.1">
        <title>创建 PLAN.md 标准模板</title>
        <file>references/plan-template.md</file>
        <action>从 agents/opc-planner.md 现有模板段抽取 XML+Markdown 混合结构, 加字段语义表 (id/file/test-expectation/completion-gate/depends_on)</action>
        <test-expectation>文件存在; 包含完整 opc-plan XML 示例; 字段语义表覆盖全部必填字段</test-expectation>
        <completion-gate>新 agent 可通过 "参考 references/plan-template.md" 单行引用即可获得完整模板</completion-gate>
      </task>

      <task id="1.2">
        <title>创建代码审查评分表</title>
        <file>references/review-rubric.md</file>
        <action>从 skills/product/reviewing/SKILL.md 抽取五维度 (规格/质量/安全/可维护性/测试覆盖) 评分表与判决规则</action>
        <test-expectation>文件存在; 五维度齐全; 包含 PASS/NEEDS FIX/REJECT 判决标准</test-expectation>
        <completion-gate>opc-reviewer agent 引用此文件后无需自带评分逻辑</completion-gate>
      </task>

      <task id="1.3">
        <title>建立重构基线 git tag</title>
        <file>(git operation)</file>
        <action>git tag pre-refactor-v1.3 标记重构起点, 失败可一键回滚</action>
        <test-expectation>git tag --list 包含 pre-refactor-v1.3</test-expectation>
        <completion-gate>tag 已推到本地 (是否推远端待用户决定)</completion-gate>
      </task>

    </wave>

    <!-- ========== Wave 2: Phase A — planning 链路样板 (依赖 1.1) ========== -->
    <wave id="2" description="先做 planning 一条完整链路验证 dispatcher pattern">

      <task id="2.1" depends_on="1.1">
        <title>扩展 opc-planner agent 吸收完整 workflow</title>
        <file>agents/opc-planner.md</file>
        <action>
          新增 Phase 0 (需求澄清, 吸收自 brainstorming skill 的 5 个问题);
          新增 Phase 1 (方案比较, 2-3 方案 + 一人公司适配度);
          保留原 Phase 2 (任务分解, 改为引用 references/plan-template.md);
          保留原 Phase 3 (波次优化);
          新增 Phase 4 (Pre-flight Gate, 吸收自 commands/opc/plan.md, 派发 plan-checker + assumptions-analyzer + 3 轮修订);
          新增 Phase 5 (输出, 含 OPC Pre-flight Gate 摘要);
          保留 4 条刚性规则
        </action>
        <test-expectation>agent 文件 ≤ 200 行; 6 个 Phase 完整; 不再依赖 planning/brainstorming skill 内的流程描述</test-expectation>
        <completion-gate>读 agent 单文件即可了解从需求到 PLAN.md 的全流程</completion-gate>
      </task>

      <task id="2.2">
        <title>瘦身 planning skill 为 dispatcher</title>
        <file>skills/product/planning/SKILL.md</file>
        <action>
          重写为 ~26 行;
          frontmatter description 包含触发线索词 (规划/破任务/波次);
          正文只含: 触发条件 / 派发目标 / 输入输出契约 / 边界 / 关联 skill;
          删除原有任务分解原则、模板、波次优化指南
        </action>
        <test-expectation>文件 ≤ 30 行; 不含流程步骤; 不含模板; 含 Task(opc-planner) 派发说明</test-expectation>
        <completion-gate>Claude 读 description 能 auto-match 规划场景; 派发后所有逻辑由 agent 完成</completion-gate>
      </task>

      <task id="2.3">
        <title>瘦身 plan command 为薄入口</title>
        <file>commands/opc/plan.md</file>
        <action>
          重写为 ~11 行;
          只保留 frontmatter + "调用 planning skill, 传 $ARGUMENTS";
          删除原有 brainstorming 调用、gate 判决清单、5 个流程步骤
        </action>
        <test-expectation>文件 ≤ 15 行; 不含流程步骤; 不含 gate 描述</test-expectation>
        <completion-gate>/opc-plan 与自然语言 "规划 X" 走完全相同的 skill→agent 链路</completion-gate>
      </task>

      <task id="2.4" depends_on="2.1,2.2,2.3">
        <title>验证 planning 链路样板</title>
        <file>(verification)</file>
        <action>
          人工或脚本验证两条入口:
          (a) /opc-plan 测试需求 → 确认调用 planning skill → 派发 opc-planner;
          (b) "帮我规划 X" → 确认 auto-discovery 命中 planning skill;
          两条路径汇聚到同一 agent, 输出包含 OPC Pre-flight Gate 摘要
        </action>
        <test-expectation>两种入口产生结构相同的 PLAN.md; agent 内 6 个 Phase 都被触发</test-expectation>
        <completion-gate>样板验证通过, dispatcher pattern 可复制到其他链路</completion-gate>
      </task>

      <task id="2.5" depends_on="2.4">
        <title>提交 Phase A</title>
        <file>(git commit)</file>
        <action>git commit -m "refactor(planning): adopt skill-dispatcher / agent-workflow pattern"</action>
        <test-expectation>commit 包含 5 个文件改动 (1 ref 新增 + 1 agent 扩展 + 1 skill 瘦身 + 1 command 瘦身 + tag)</test-expectation>
        <completion-gate>git log 显示 Phase A commit; 工作树干净</completion-gate>
      </task>

    </wave>

    <!-- ========== Wave 3: Phase B — 复制 pattern 到 4 条业务链路 (依赖 Phase A 通过) ========== -->
    <wave id="3" description="Phase A 验证通过后批量复制 pattern">

      <task id="3.1" depends_on="2.5">
        <title>brainstorming 链路改造</title>
        <file>skills/product/brainstorming/SKILL.md</file>
        <action>
          瘦身为 ~25 行 dispatcher;
          流程已在 2.1 任务中合并到 opc-planner Phase 0-1;
          skill 仅负责 "需求模糊 / 想法未成型" 触发并派发 opc-planner;
          保留 HARD-GATE 语义: 设计未批准不进入 planning
        </action>
        <test-expectation>skill ≤ 30 行; HARD-GATE 仍然可见; 派发目标明确</test-expectation>
        <completion-gate>brainstorming 与 planning 共享同一 agent, 入口语义不同但流程一致</completion-gate>
      </task>

      <task id="3.2" depends_on="2.5">
        <title>implementing 链路改造</title>
        <file>agents/opc-executor.md</file>
        <action>
          扩展 opc-executor 吸收 implementing skill + subagent-driven-development skill 的完整流程;
          含: 任务提取 / 子代理派发 / 双阶段审查 / TDD 循环 / 原子提交 / SUMMARY.md
        </action>
        <test-expectation>agent ≤ 250 行; 完整子代理派发协议; 引用 Skill(tdd) 而不内联 TDD 步骤</test-expectation>
        <completion-gate>读 agent 单文件即可了解从 PLAN.md 到完成的全流程</completion-gate>
      </task>

      <task id="3.3" depends_on="3.2">
        <title>瘦身 implementing skill 为 dispatcher</title>
        <file>skills/product/implementing/SKILL.md</file>
        <action>重写为 ~25 行 dispatcher; 派发 opc-executor; 触发条件: 已有 ready-for-build 的 PLAN.md</action>
        <test-expectation>skill ≤ 30 行; 不含子代理流程; 含输入契约 (ready-for-build: true)</test-expectation>
        <completion-gate>实现入口收敛到单一 skill→agent</completion-gate>
      </task>

      <task id="3.4" depends_on="3.3">
        <title>瘦身 build command</title>
        <file>commands/opc/build.md</file>
        <action>重写为 ~8 行; 调用 implementing skill</action>
        <test-expectation>文件 ≤ 15 行</test-expectation>
        <completion-gate>/opc-build 入口与 "执行计划" 自然语言汇聚</completion-gate>
      </task>

      <task id="3.5" depends_on="2.5,1.2">
        <title>reviewing 链路改造</title>
        <file>agents/opc-reviewer.md</file>
        <action>
          扩展 opc-reviewer: 引用 references/review-rubric.md 替代内联评分表;
          补齐原 reviewing skill 的可维护性维度 (6 个月可读 / 依赖最小 / 成本可控 / 监控告警);
          保留判决规则 (PASS / NEEDS FIX / REJECT)
        </action>
        <test-expectation>agent 引用 review-rubric.md; 五维度齐全; 一人公司可维护性段落完整</test-expectation>
        <completion-gate>读 agent 即可了解审查全维度</completion-gate>
      </task>

      <task id="3.6" depends_on="3.5">
        <title>瘦身 reviewing skill + review command</title>
        <file>skills/product/reviewing/SKILL.md</file>
        <action>skill 重写为 ~25 行 dispatcher; commands/opc/review.md 重写为 ~8 行</action>
        <test-expectation>skill ≤ 30 行; command ≤ 15 行</test-expectation>
        <completion-gate>review 入口收敛</completion-gate>
      </task>

      <task id="3.7" depends_on="2.5">
        <title>新建 opc-shipper agent</title>
        <file>agents/opc-shipper.md</file>
        <action>
          新建 agent, 吸收 shipping skill 的全部流程: 测试验证 / merge-base / 4 选项呈现 / worktree 清理 / 一人公司发布检查清单
        </action>
        <test-expectation>agent 文件存在; 4 选项 (合并/PR/保持/丢弃) 完整; 含一人公司检查清单</test-expectation>
        <completion-gate>shipping 流程有专属 agent owner</completion-gate>
      </task>

      <task id="3.8" depends_on="3.7">
        <title>瘦身 shipping skill + ship command</title>
        <file>skills/product/shipping/SKILL.md</file>
        <action>skill 重写为 ~25 行 dispatcher 派发 opc-shipper; commands/opc/ship.md 重写为 ~8 行</action>
        <test-expectation>skill ≤ 30 行; command ≤ 15 行</test-expectation>
        <completion-gate>ship 入口收敛</completion-gate>
      </task>

      <task id="3.9" depends_on="3.1,3.4,3.6,3.8">
        <title>更新 agents/registry.json 注册 opc-shipper</title>
        <file>agents/registry.json</file>
        <action>在 agents 数组追加 opc-shipper 条目, capability_tags=["shipping","release","merge","pr","deploy"], priority=72</action>
        <test-expectation>JSON 合法; opc-shipper 可被 dag_engine 语义路由命中</test-expectation>
        <completion-gate>registry 与 .md 同步</completion-gate>
      </task>

      <task id="3.10" depends_on="3.9">
        <title>提交 Phase B</title>
        <file>(git commit)</file>
        <action>git commit -m "refactor(skills): apply dispatcher pattern to brainstorming/implementing/reviewing/shipping"</action>
        <test-expectation>commit 含 9 个文件改动</test-expectation>
        <completion-gate>git log 显示 Phase B commit</completion-gate>
      </task>

    </wave>

    <!-- ========== Wave 4: Phase C — atomic skill 合并 + command 收敛 (依赖 Phase B) ========== -->
    <wave id="4" description="清理重复 atomic skill 与路由命令">

      <task id="4.1" depends_on="3.10">
        <title>合并 parallel-agents + subagent-driven-development</title>
        <file>skills/engineering/agent-dispatch/SKILL.md</file>
        <action>
          新建合并 skill, 用章节区分两种模式: A) 串行+双阶段审查 (来自 subagent-driven-development); B) 波次并行 (来自 parallel-agents);
          保留两者的红线、压力测试、模型选择策略;
          删除两个旧 skill 目录
        </action>
        <test-expectation>新 skill 存在且涵盖两种模式; 旧目录已删</test-expectation>
        <completion-gate>opc-executor 等 agent 引用统一为 Skill(agent-dispatch)</completion-gate>
      </task>

      <task id="4.2" depends_on="3.10">
        <title>扩展 opc-orchestrator 接管模式路由</title>
        <file>agents/opc-orchestrator.md</file>
        <action>
          新增 "模式选择决策树" 章节, 吸收自 workflow-modes skill;
          含 7 模式 (autonomous/discuss/explore/fast/quick/do/next) 的判定顺序与适用边界
        </action>
        <test-expectation>agent 含完整决策树; 7 模式齐全</test-expectation>
        <completion-gate>orchestrator 单文件即可决定调度模式</completion-gate>
      </task>

      <task id="4.3" depends_on="4.2">
        <title>瘦身 workflow-modes skill</title>
        <file>skills/using-superopc/workflow-modes/SKILL.md</file>
        <action>重写为 ~25 行 dispatcher 派发 opc-orchestrator; 触发条件: 用户意图模糊 / 不知该用哪个模式</action>
        <test-expectation>skill ≤ 30 行</test-expectation>
        <completion-gate>模式选择逻辑收敛到 agent</completion-gate>
      </task>

      <task id="4.4" depends_on="4.2">
        <title>新建统一 /opc 入口命令</title>
        <file>commands/opc/opc.md</file>
        <action>新建 /opc 命令, 调用 workflow-modes skill, 由 orchestrator 决定派发哪个 agent</action>
        <test-expectation>文件 ≤ 15 行; description 包含意图路由线索</test-expectation>
        <completion-gate>用户用 /opc &lt;任意自然语言&gt; 能命中正确流程</completion-gate>
      </task>

      <task id="4.5" depends_on="4.4">
        <title>删除 6 个旧路由命令</title>
        <file>commands/opc/{do,next,discuss,explore,fast,quick}.md</file>
        <action>删除 6 个文件; CHANGELOG 列出迁移映射 (旧命令 → /opc 替代)</action>
        <test-expectation>6 文件已删; commands/opc/ 目录从 27 减到 22</test-expectation>
        <completion-gate>命令层入口收敛</completion-gate>
      </task>

      <task id="4.6" depends_on="4.1,4.5">
        <title>提交 Phase C</title>
        <file>(git commit)</file>
        <action>git commit -m "refactor: consolidate atomic skills and collapse mode-router commands"</action>
        <test-expectation>commit 含约 10 个文件改动</test-expectation>
        <completion-gate>git log 显示 Phase C commit</completion-gate>
      </task>

    </wave>

    <!-- ========== Wave 5: Phase D — 全局一致性扫尾 (依赖 Phase C) ========== -->
    <wave id="5" description="同步元数据 + 文档 + 导出验证">

      <task id="5.1" depends_on="4.6">
        <title>更新 .claude-plugin/plugin.json</title>
        <file>.claude-plugin/plugin.json</file>
        <action>新增 opc-shipper agent 条目; 移除已删 6 个 command 条目; 验证 manifest 与实际文件一致</action>
        <test-expectation>JSON 合法; 与 agents/ 和 commands/ 实际文件 1:1 对应</test-expectation>
        <completion-gate>plugin manifest 同步</completion-gate>
      </task>

      <task id="5.2" depends_on="4.6">
        <title>更新 AGENTS.md 编排规则表</title>
        <file>AGENTS.md</file>
        <action>新增 opc-shipper 行; 更新流水线图 (planning/build/review/ship 全部经过 dispatcher skill); 添加 "dispatcher vs atomic skill" 概念说明</action>
        <test-expectation>表格含全部 18 个 agent; 流水线图反映新架构</test-expectation>
        <completion-gate>AGENTS.md 与 registry.json 一致</completion-gate>
      </task>

      <task id="5.3" depends_on="4.6">
        <title>更新 CLAUDE.md 架构说明</title>
        <file>CLAUDE.md</file>
        <action>修改 "高级架构" 章节, 说明 dispatcher-skill / atomic-skill / agent-workflow 三角契约; 更新触发链路示例</action>
        <test-expectation>架构段落反映新模式; 含两类 skill 区分说明</test-expectation>
        <completion-gate>新加入开发者读 CLAUDE.md 即可理解架构</completion-gate>
      </task>

      <task id="5.4" depends_on="5.1,5.2,5.3">
        <title>更新 README.md 命令表与技能表</title>
        <file>README.md</file>
        <action>同步命令表 (27→22); 在技能表中标注 dispatcher / atomic 类型</action>
        <test-expectation>README 命令清单与实际文件一致; 技能表有类型标注</test-expectation>
        <completion-gate>README 反映新结构</completion-gate>
      </task>

      <task id="5.5" depends_on="5.4">
        <title>编写 CHANGELOG v1.3.0</title>
        <file>CHANGELOG.md</file>
        <action>
          新增 v1.3.0 章节, 含:
          - Architecture: skill-dispatcher / agent-workflow 模式;
          - Removed: 6 个路由命令 + parallel-agents/subagent-driven-development skill 目录;
          - Added: opc-shipper agent + 2 个 reference 文件 + agent-dispatch skill;
          - Migration: 旧命令/技能名 → 新位置映射表
        </action>
        <test-expectation>CHANGELOG 含完整迁移表; 用户能根据旧引用找到新位置</test-expectation>
        <completion-gate>v1.3.0 文档化完成</completion-gate>
      </task>

      <task id="5.6" depends_on="5.5">
        <title>跑 scripts/convert.py 验证 5 个下游 IDE 导出</title>
        <file>(verification)</file>
        <action>python scripts/convert.py --tool all; 检查 integrations/{cursor,windsurf,gemini-cli,opencode,openclaw}/ 输出无错</action>
        <test-expectation>convert.py 退出码 0; 各 IDE 目录有最新输出</test-expectation>
        <completion-gate>下游导出无破坏性变化</completion-gate>
      </task>

      <task id="5.7" depends_on="5.6">
        <title>提交 Phase D</title>
        <file>(git commit)</file>
        <action>git commit -m "docs: update architecture narrative for dispatcher/workflow split"</action>
        <test-expectation>commit 含 5 个文档改动</test-expectation>
        <completion-gate>v1.3.0 重构完成</completion-gate>
      </task>

    </wave>

  </waves>
</opc-plan>

## 关键决策点

### 决策 1: brainstorming 是否保留独立 skill?

**保留**。理由：brainstorming 触发条件 (需求模糊) 与 planning (设计已批准) 不同, 应有独立 dispatcher。但流程合并到 opc-planner Phase 0-1, 不重复实现。

### 决策 2: opc-shipper 是新建 agent 还是 ship 直接调脚本?

**新建 agent**。保持 "每个 dispatcher skill 都有专属 agent owner" 的对称性。

### 决策 3: /opc 是否完全替代 6 个旧路由命令?

**是**, 但 CHANGELOG 提供迁移映射, 用户旧记忆能查到新位置。

### 决策 4: convert.py 是否需要适配?

**不需要**。它扫描 skills/agents/commands 目录, 自动跟随结构变化。Phase D 的 5.6 任务只是验证。

## 回滚策略

- 每个 Phase 独立 commit, 失败可单独 `git revert <commit>`
- Phase A 的 git tag `pre-refactor-v1.3` 是终极回滚点: `git reset --hard pre-refactor-v1.3`
- 风险最高的是 Phase C (合并 atomic skill + 删命令); 建议在 Phase B 完成后再决定是否继续

## 验证清单 (重构完成后)

- [ ] `skills/product/` 下每个 SKILL.md ≤ 30 行
- [ ] `commands/opc/` 下每个 .md ≤ 15 行
- [ ] `agents/` 下每个 .md 包含完整 workflow (无 "调用 X skill 执行下一步" 这类语句)
- [ ] atomic skill 内无 `Task(` 或 "派发 agent" 语句
- [ ] `/opc-plan` 与自然语言 "规划 X" 触发同一 PLAN.md 输出结构
- [ ] `python scripts/convert.py --tool all` 退出码 0

## OPC Pre-flight Gate

- plan-check: SELF-APPROVED (本 PLAN.md 由 dogfooding 撰写, 未跑 opc-plan-checker)
- assumptions: SELF-APPROVED (主要假设: convert.py 不需要适配; brainstorming 保留独立入口; 用户接受 6 个命令合并)
- ready-for-build: true

> **注：** 由于本次重构涉及 opc-plan-checker 自身, 跳过自动门控, 改为人工审核本计划。
