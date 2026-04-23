# SuperOPC v1.4.0 — Skill 精简（skill-dispatcher 模式收尾）实施计划

> 承接 v1.3 Phase A–D（Skill-Dispatcher / Agent-Workflow 契约），把仍然内联
> workflow 或仅作知识库用的 skill 全部下沉到 `references/` 或 `agents/`，
> 让 skill 空间只剩下真正驱动 agent workflow 的派发器 + 刚性原子技能。
>
> **目标数量：53 → 14**。每个剩下的 skill 能一句话回答"我驱动哪个 agent
> 的哪个 workflow"或"我是哪个刚性纪律"。

<opc-plan>
  <metadata>
    <goal>把 SuperOPC 的 skill 空间精简为 14 个纯派发器 / 原子技能；workflow 全部归属 agent；知识库全部下沉到 references/</goal>
    <spec-url>docs/archive/REFACTOR-PLAN.md + docs/plans/2026-04-17-architecture-refactor.md（前置 v1.3 重构）</spec-url>
    <estimated-time>4-6h（5 waves × 原子 commit）</estimated-time>
  </metadata>

  <waves>

    <wave id="1" description="知识库迁移：把纯参考内容搬到 references/，不改内容本身（只搬位置）">
      <task id="1.1">
        <title>技术栈 patterns → references/patterns/engineering/</title>
        <file>skills/engineering/{api-design,architecture-decision-records,backend-patterns,codebase-onboarding,database-migrations,deployment-patterns,docker-patterns,dotnet-patterns,e2e-testing,frontend-patterns,kotlin-compose,nextjs-patterns,postgres-patterns}/ → references/patterns/engineering/*.md</file>
        <action>批量 git mv 13 个 engineering/*-patterns skill 到 references/patterns/engineering/&lt;name&gt;.md（展平目录，去掉 SKILL.md 文件名，SKILL frontmatter 保留但标题改为普通 markdown）；commit 消息 `refactor(skills): 技术栈 patterns 下沉到 references/patterns/engineering/`</action>
        <test-expectation>git log 显示 13 个 rename；ls skills/engineering 不再有 *-patterns / api-design / architecture-decision-records / codebase-onboarding / database-migrations / deployment-patterns / docker-patterns / dotnet-patterns / e2e-testing / kotlin-compose；ls references/patterns/engineering 出现 13 个 .md</test-expectation>
        <completion-gate>git status 干净；references/patterns/engineering/ 下文件数 = 13；没有内容丢失（git diff 所有行数守恒）</completion-gate>
      </task>

      <task id="1.2">
        <title>商业方法论 → references/business/</title>
        <file>skills/business/{brand-voice,company-values,content-engine,daily-standup,finance-ops,find-community,first-customers,grow-sustainably,investor-materials,legal-basics,marketing-plan,minimalist-review,mvp,pricing,processize,product-lens,seo,thirty-day-launch,user-interview,validate-idea}/ → references/business/*.md</file>
        <action>批量 git mv 20 个 business skill 到 references/business/&lt;name&gt;.md（展平目录）；commit `refactor(skills): 商业方法论下沉到 references/business/`</action>
        <test-expectation>git log 显示 20 个 rename；ls skills/business 为空目录（将在 wave 3 用于 advisory dispatcher）；ls references/business 出现 20 个 .md</test-expectation>
        <completion-gate>git status 干净；references/business/ 下文件数 = 20</completion-gate>
      </task>

      <task id="1.3">
        <title>intelligence 部分下沉 + autonomous-ops 归位</title>
        <file>skills/intelligence/{market-research,follow-builders}/ → references/intelligence/*.md；skills/intelligence/autonomous-ops/ → skills/using-superopc/autonomous-ops/</file>
        <action>git mv market-research 与 follow-builders 两项到 references/intelligence/；git mv autonomous-ops 到 using-superopc/autonomous-ops/（它是 cruise controller 的规则，更贴合元层）；commit `refactor(skills): intelligence 参考化，autonomous-ops 归入元层`</action>
        <test-expectation>skills/intelligence 目录被删除；references/intelligence 出现 2 个 .md；skills/using-superopc/autonomous-ops/SKILL.md 存在</test-expectation>
        <completion-gate>git status 干净</completion-gate>
      </task>

      <task id="1.4">
        <title>learning 合并：skill-from-masters + writing-skills → references/skill-authoring.md</title>
        <file>skills/learning/{skill-from-masters,writing-skills}/SKILL.md → references/skill-authoring.md</file>
        <action>读两个旧 SKILL.md 内容，合并为 `references/skill-authoring.md`（章节：从大师提取方法论 + 撰写新 skill 规范）；git rm 两个旧 skill 目录；只保留 skills/learning/continuous-learning/；commit `refactor(skills): skill-authoring 参考化，learning 只留 continuous-learning`</action>
        <test-expectation>skills/learning 只剩 continuous-learning；references/skill-authoring.md 存在且包含两个旧 skill 的核心指引</test-expectation>
        <completion-gate>grep -c '^##' references/skill-authoring.md ≥ 4（至少两个主章节 + 子节）；git status 干净</completion-gate>
      </task>

      <task id="1.5">
        <title>code-review-pipeline 细则并入 references/review-rubric.md</title>
        <file>skills/engineering/code-review-pipeline/SKILL.md → references/review-rubric.md（扩展）+ 删 skill</file>
        <action>读 code-review-pipeline SKILL.md（146 行），提取 Quick / Standard / Deep 三级审查清单 + 审查流程 + 报告格式，合入 `references/review-rubric.md` 新增章节；git rm 旧 skill 目录；commit `refactor(skills): code-review-pipeline 合入 review-rubric，删除重复 skill`</action>
        <test-expectation>references/review-rubric.md 含 Quick/Standard/Deep 三级章节；skills/engineering/code-review-pipeline 目录被删除</test-expectation>
        <completion-gate>grep -E 'Quick|Standard|Deep' references/review-rubric.md 命中；git status 干净</completion-gate>
      </task>
    </wave>

    <wave id="2" description="Agent 扩展 / 新建：把原本内联在 skill 里的 workflow 移交给 agent">
      <task id="2.1">
        <title>新建 agents/opc-business-advisor.md</title>
        <file>agents/opc-business-advisor.md</file>
        <action>新建 agent 文件（model: sonnet；tools: Read/Write/Edit/Grep/Glob/TodoWrite/Skill/Task），持有一人公司商业活动完整 workflow：Phase 0 识别子活动（20 个：pricing / mvp / validate-idea / first-customers / find-community / processize / ...）→ Phase 1 按子活动加载 references/business/&lt;name&gt;.md → Phase 2 按该方法论执行（问卷 / 清单 / 报告）→ Phase 3 产出决策建议。HARD-GATE：涉及 "构建产品" 前必须先走 validate-idea + find-community（Anti-Build-Trap）。commit `feat(agents): 新增 opc-business-advisor 持有商业 workflow`</action>
        <test-expectation>agents/opc-business-advisor.md 存在；包含 frontmatter（name、description、tools、model）；含 Phase 0-3 完整 workflow 描述；显式引用 references/business/ 作为方法论源</test-expectation>
        <completion-gate>grep -E '^name: opc-business-advisor' agents/opc-business-advisor.md 命中；wc -l ≥ 120</completion-gate>
      </task>

      <task id="2.2">
        <title>扩展 agents/opc-reviewer.md 吸收 Quick/Standard/Deep 三级审查</title>
        <file>agents/opc-reviewer.md</file>
        <action>在现有 5 维评审基础上增加"审查深度选择"章节：根据变更规模 / 风险等级选择 Quick(5min) / Standard(15-30min) / Deep(1-2h)；引用 `references/review-rubric.md` 获取清单；commit `refactor(agents): opc-reviewer 吸收三级审查深度`</action>
        <test-expectation>opc-reviewer.md 含深度选择决策树；grep -E 'Quick|Standard|Deep' 命中</test-expectation>
        <completion-gate>文件行数增量 ≥ 30；引用 review-rubric.md 至少一处</completion-gate>
      </task>

      <task id="2.3">
        <title>扩展 agents/opc-security-auditor.md 吸收 OWASP workflow</title>
        <file>agents/opc-security-auditor.md + references/security-checklist.md（新建）</file>
        <action>把 `skills/engineering/security-review/SKILL.md` 的 OWASP Top 10 清单 + 报告格式抽取到新 `references/security-checklist.md`；opc-security-auditor.md 扩展为完整 workflow 持有者（Phase 0 范围确认 → Phase 1 按 OWASP 10 个类别扫描 → Phase 2 输出严重级别分布报告）；commit `refactor(agents): opc-security-auditor 吸收 OWASP 全 workflow`</action>
        <test-expectation>references/security-checklist.md 存在含 A01-A10；opc-security-auditor.md 含 Phase 0-2 并引用 security-checklist.md</test-expectation>
        <completion-gate>grep -E 'A0[1-9]|A10' references/security-checklist.md ≥ 10 次命中</completion-gate>
      </task>

      <task id="2.4">
        <title>扩展 agents/opc-debugger.md 吸收 debugging 细则</title>
        <file>agents/opc-debugger.md</file>
        <action>把 `skills/engineering/debugging/SKILL.md` 的"假设-证据-排除"循环、红绿黄日志策略等细则吸收到 opc-debugger.md，作为完整 workflow 持有者；commit `refactor(agents): opc-debugger 吸收 debugging workflow 细则`</action>
        <test-expectation>opc-debugger.md 行数增量 ≥ 40；含"假设-证据-排除"关键词</test-expectation>
        <completion-gate>grep -E '假设|证据|排除' agents/opc-debugger.md 命中</completion-gate>
      </task>

      <task id="2.5">
        <title>agents/registry.json 注册 opc-business-advisor</title>
        <file>agents/registry.json</file>
        <action>添加 opc-business-advisor 条目：capability_tags=[pricing, validate-idea, first-customers, mvp, marketing, seo, ...] / scenarios=[方案调研, 定价, 获客, 增长] / priority=75 / input=natural-language / output=决策建议 + 可选 SUMMARY.md；commit `feat(registry): 注册 opc-business-advisor 供 DAG 语义路由`</action>
        <test-expectation>jq '.agents["opc-business-advisor"]' agents/registry.json 返回非空</test-expectation>
        <completion-gate>python -c "import json; d=json.load(open('agents/registry.json','r',encoding='utf-8')); assert 'opc-business-advisor' in d.get('agents',{})" 退出码 0</completion-gate>
      </task>
    </wave>

    <wave id="3" description="Dispatcher skill 新建 / 瘦身 / 删除（依赖 Wave 2 的 agent 到位）">
      <task id="3.1" depends_on="2.1,2.5">
        <title>新建 skills/business/advisory/SKILL.md 派发器</title>
        <file>skills/business/advisory/SKILL.md</file>
        <action>新建 ≤30 行 dispatcher skill，description 覆盖所有商业场景触发词（定价 / MVP / 验证想法 / 找社区 / 获客 / 营销 / SEO / 法务 / 财务 / 增长 / ...），调用 Task(opc-business-advisor)；引用 references/business/ 作为方法论源；宣言：Anti-Build-Trap 在 advisor 内部执行；commit `feat(skills): 新增 business/advisory 派发器统一接入 opc-business-advisor`</action>
        <test-expectation>skills/business/advisory/SKILL.md 存在；行数 ≤30；description 覆盖 5+ 商业关键词；无内联 workflow</test-expectation>
        <completion-gate>wc -l ≤ 30；grep -c '^##' ≤ 5（纯 dispatcher 结构）</completion-gate>
      </task>

      <task id="3.2" depends_on="2.3">
        <title>skills/engineering/security-review/SKILL.md 瘦成 dispatcher</title>
        <file>skills/engineering/security-review/SKILL.md</file>
        <action>重写为 ≤30 行纯派发器，Task(opc-security-auditor)；OWASP 清单移除（已在 references/security-checklist.md）；commit `refactor(skills): security-review 瘦成派发器指向 opc-security-auditor`</action>
        <test-expectation>wc -l ≤ 30；无内联 OWASP 清单</test-expectation>
        <completion-gate>grep -c 'A0[1-9]\|A10' 返回 0（清单全部移除）</completion-gate>
      </task>

      <task id="3.3" depends_on="2.4">
        <title>skills/engineering/debugging/SKILL.md 瘦成 dispatcher</title>
        <file>skills/engineering/debugging/SKILL.md</file>
        <action>重写为 ≤30 行 dispatcher，Task(opc-debugger)；细则已在 agent 内；commit `refactor(skills): debugging 瘦成派发器指向 opc-debugger`</action>
        <test-expectation>wc -l ≤ 30；无内联 workflow 步骤</test-expectation>
        <completion-gate>grep -E '^## ' | wc -l ≤ 4</completion-gate>
      </task>

      <task id="3.4">
        <title>验证 skill 最终数量 = 14</title>
        <file>（全目录校验）</file>
        <action>运行 `python -c "from pathlib import Path; skills = list(Path('skills').rglob('SKILL.md')); print(len(skills)); [print(s) for s in skills]"`；预期 14 项：using-superopc/SKILL + session-management + workflow-modes + developer-profile + autonomous-ops（5）+ product/{brainstorming,planning,implementing,reviewing,shipping}（5）+ engineering/{tdd,debugging,verification-loop,agent-dispatch,security-review,git-worktrees}（6）+ business/advisory（1）+ learning/continuous-learning（1）+ intelligence/（可能 0）= 18 → 需要再砍</action>
        <test-expectation>本任务只计数，若 &gt;14 则生成调整任务追加到 wave 3</test-expectation>
        <completion-gate>列表输出与预期一致，或差异明确列出待后续处理</completion-gate>
      </task>
    </wave>

    <wave id="4" description="元文档同步（依赖 Wave 1-3 全部完成）">
      <task id="4.1" depends_on="3.4">
        <title>skills/using-superopc/SKILL.md 重写技能表</title>
        <file>skills/using-superopc/SKILL.md</file>
        <action>重写"技能体系"章节，仅列 14 个 skill（按派发器/原子/元/学习分组）；每行明确映射到 agent 或说明是原子纪律；commit `docs(meta): 重写 using-superopc 技能表为精简后 14 项`</action>
        <test-expectation>文件中列出的 skill 数量 = 实际目录下 SKILL.md 数量</test-expectation>
        <completion-gate>grep -E '^\| \*\*[a-z-]+\*\*' skills/using-superopc/SKILL.md 计数 = 14 ± 2</completion-gate>
      </task>

      <task id="4.2" depends_on="3.4">
        <title>CLAUDE.md 更新 Skills 章节</title>
        <file>CLAUDE.md</file>
        <action>重写第 103-128 行附近的 Skills 章节：明确 "Dispatcher skills（7）+ Atomic skills（4）+ Meta skills（3）= 14"；技术栈 patterns / 商业 playbook 标注为 references/；commit `docs(claude): 同步 v1.4 精简后 skill 分类`</action>
        <test-expectation>CLAUDE.md Skills 章节明确列出 14 个；references/patterns/ + references/business/ 被提及</test-expectation>
        <completion-gate>grep -c 'references/patterns\|references/business' CLAUDE.md ≥ 2</completion-gate>
      </task>

      <task id="4.3" depends_on="2.1,2.5">
        <title>AGENTS.md 更新 dispatcher 映射表 + 新 agent</title>
        <file>AGENTS.md</file>
        <action>代理编排表增加 opc-business-advisor 行（触发入口：business/advisory skill）；删除已失效的 skill 映射；更新 v1.3 → v1.4 迁移表；commit `docs(agents): 同步 v1.4 新 agent 与精简 skill 映射`</action>
        <test-expectation>AGENTS.md 表格含 opc-business-advisor 行；v1.4 迁移表存在</test-expectation>
        <completion-gate>grep -c 'opc-business-advisor' AGENTS.md ≥ 2</completion-gate>
      </task>

      <task id="4.4" depends_on="3.4">
        <title>README.md 更新 skill tree / 命令树</title>
        <file>README.md / README_EN.md</file>
        <action>更新目录展示（14 skill + 17→18 agents）；新增 references/patterns/ + references/business/ 介绍；commit `docs(readme): 更新 v1.4 架构图与目录清单`</action>
        <test-expectation>README.md 中 skill 数量描述与实际一致</test-expectation>
        <completion-gate>grep -c '14' README.md ≥ 1（或按实际数量）</completion-gate>
      </task>

      <task id="4.5" depends_on="2.1">
        <title>.claude-plugin/plugin.json 同步</title>
        <file>.claude-plugin/plugin.json</file>
        <action>如果 plugin.json 显式列出 skill / agent，补充 opc-business-advisor，移除已删除 skill（code-review-pipeline, skill-from-masters, writing-skills）；commit `chore(plugin): 同步 v1.4 新 agent 与删除 skill`</action>
        <test-expectation>python -c "import json; json.load(open('.claude-plugin/plugin.json'))" 不报错；内容与实际目录一致</test-expectation>
        <completion-gate>jq '.' .claude-plugin/plugin.json 退出码 0</completion-gate>
      </task>

      <task id="4.6" depends_on="4.1,4.2,4.3">
        <title>CHANGELOG.md 写入 v1.4.0 完整条目</title>
        <file>CHANGELOG.md</file>
        <action>新增 v1.4.0 章节：架构契约延续（skill 精简完成）+ 新增 opc-business-advisor + 删除 skill 清单 + 搬迁清单 + 兼容性说明（外部引用如何迁移）+ 回滚策略（tag pre-refactor-v1.4）；commit `docs(changelog): v1.4.0 skill 精简完整条目`</action>
        <test-expectation>CHANGELOG.md 含 v1.4.0 + 子章节：Added / Changed / Removed / Migration / Rollback</test-expectation>
        <completion-gate>grep -E '^## \[1\.4\.0\]' CHANGELOG.md 命中</completion-gate>
      </task>

      <task id="4.7">
        <title>ROADMAP.md 标注 v1.4.0 完成</title>
        <file>ROADMAP.md</file>
        <action>更新 v1.4.0 行的状态为已完成，填入交付摘要；commit `docs(roadmap): v1.4.0 已完成`</action>
        <test-expectation>ROADMAP.md 中 v1.4.0 行标记完成</test-expectation>
        <completion-gate>grep -E 'v1\.4\.0.*✅|已完成' ROADMAP.md 命中</completion-gate>
      </task>
    </wave>

    <wave id="5" description="验证 + 打 tag + 推送（依赖全部前面完成）">
      <task id="5.1" depends_on="4.6">
        <title>scripts/convert.py --tool all 全量验证</title>
        <file>（执行检查）</file>
        <action>运行 `python scripts/convert.py --tool all`；预期所有 11 个下游运行时 exit 0；截取输出长度、items 计数验证；commit `chore(verify): v1.4 convert.py 全量通过`（若 convert.py 无生成 diff 则无需 commit）</action>
        <test-expectation>退出码 0；items × 11 ≈ 新 skill+agent+command 数量</test-expectation>
        <completion-gate>退出码 0；stderr 无错误</completion-gate>
      </task>

      <task id="5.2" depends_on="4.6">
        <title>scripts/opc_health.py 通过</title>
        <file>（执行检查）</file>
        <action>运行 `python scripts/opc_health.py`（或等价脚本）检查内部链接、frontmatter、plugin wiring；commit 同上（若需）</action>
        <test-expectation>退出码 0</test-expectation>
        <completion-gate>退出码 0；无 broken link</completion-gate>
      </task>

      <task id="5.3" depends_on="5.1,5.2">
        <title>打 tag pre-refactor-v1.4 + 推送</title>
        <file>（Git 操作）</file>
        <action>在 Wave 5 开始前提交处打 `git tag pre-refactor-v1.4`（实际应在 Wave 1 开始前打）；Wave 5 结束后 `git push origin main && git push origin pre-refactor-v1.4`</action>
        <test-expectation>远端 main 与本地同步；tag 存在</test-expectation>
        <completion-gate>git ls-remote --tags origin pre-refactor-v1.4 非空</completion-gate>
      </task>
    </wave>

  </waves>
</opc-plan>

## OPC Plan Check

（自审 — 因当前环境不能 Task(opc-plan-checker)，以 opc-planner 自检代之）

| 维度 | 评估 | 备注 |
|---|---|---|
| **目标清晰** | ✅ PASS | "53 → 14" 可验证数字目标，每个剩下的 skill 有明确定位 |
| **任务原子** | ⚠️ WARN | Task 1.1 批量 mv 13 个文件在一个 commit 内不算原子；建议拆成 4 个 commit（按语言分组：web patterns / dotnet+kotlin / postgres+docker / deployment+testing+ADR），或接受"目录级原子"口径 |
| **依赖正确** | ✅ PASS | Wave 1（搬迁）独立；Wave 2（agent 扩展）需要 Wave 1.5 移除旧 skill；Wave 3（dispatcher）依赖 Wave 2；Wave 4（元文档）依赖全部；Wave 5（验证）依赖全部。显式 `depends_on` 标注 |
| **测试覆盖** | ✅ PASS | 每任务都有可验证的 `<test-expectation>` + `<completion-gate>` |
| **文件路径** | ✅ PASS | 所有任务列出具体路径 |
| **风险识别** | ✅ PASS | 见下面 Assumptions |
| **回滚方案** | ✅ PASS | Wave 5 打 tag `pre-refactor-v1.4` 前后各一个锚点；每 wave 可独立 revert |
| **一人公司适配** | ✅ PASS | 4-6h 工期合理；未引入新基础设施；长期降低维护成本（从 53 个 skill 维护降到 14 个） |

**判决：APPROVED，但 Task 1.1 / 1.2 需要拆分 commit 粒度。**

调整：Wave 1.1 拆为 4 个子 commit（web / dotnet+kotlin / postgres+docker / deployment+testing+ADR+codebase-onboarding+api-design+database-migrations）；Wave 1.2 拆为 3 个子 commit（validation+GTM / monetization+finance / marketing+content+community）。在执行时落实。

## OPC Assumptions Analysis

### 技术假设

1. **T1: `git mv` 保留历史** — ✅ 已知成立，v1.3 Phase C 已实战验证过
2. **T2: skill 发现机制不关心 frontmatter 所在目录深度** — ⚠️ 需验证。references/ 下的 md 不会被 Claude Code 的 skill 自动发现机制拾取（这正是我们想要的）；搬迁后 Claude 不再把它们当 skill 触发
3. **T3: scripts/convert.py 只遍历 skills/ + agents/ + commands/** — ⚠️ 需在 Wave 5 前读 convert.py 源码确认。若它遍历了 references/，需同步更新排除规则
4. **T4: .claude-plugin/plugin.json 不硬编码 skill 清单** — ⚠️ Wave 4.5 需先读 plugin.json 确认格式

### 用户假设

1. **U1: 外部文档 / 外部项目可能引用了旧 skill 名称** — ✅ 已缓解。CHANGELOG v1.4.0 提供迁移表；AGENTS.md 迁移映射表保留 v1.3 → v1.4
2. **U2: 用户期望保留 `pricing` 等自然语言入口能命中对应资源** — ✅ 已缓解。opc-business-advisor 的 description 覆盖所有子活动关键词；Claude 发现 business/advisory dispatcher 后由 advisor Phase 0 按关键词路由到 references/business/pricing.md

### 商业假设

1. **B1: 减少 skill 数量不会降低平台能力** — ✅ 能力全部保留在 references/ + agent workflow；只改变了发现机制和驱动关系
2. **B2: 一人公司长期更愿意维护 14 个 skill 而非 53 个** — ✅ 符合一人公司 "小步快跑 + 低维护" 原则

### 运维假设

1. **O1: CI/hooks 不依赖被删除的 skill 名称** — ⚠️ Wave 5 `opc_health.py` 会检测；若失败则 Wave 5.2 内修复
2. **O2: tag `pre-refactor-v1.3` 与 `pre-refactor-v1.4` 并存不冲突** — ✅ git tag 命名空间独立
3. **O3: 远端 main 推送不需强推** — ✅ v1.4 所有 commit 是新 commit，fast-forward 即可（不像 v1.3 rewording 那样需要 --force-with-lease）

### 高风险假设缓解

- **T3 风险（convert.py 可能依赖旧目录结构）** → 新增 **Wave 0.1 前置检查任务**：Wave 1 开始前先读 `scripts/convert.py` 前 100 行确认遍历范围；若发现依赖 skills/engineering/*-patterns 的硬编码则加入 Wave 4 更新 convert.py
- **T4 风险（plugin.json 可能硬编码）** → 新增 **Wave 0.2**：读 plugin.json 决定 Wave 4.5 改动方式
- **O1 风险（hooks 依赖）** → Wave 5.2 opc_health.py 失败视为阻塞 P1

## OPC Pre-flight Gate

- plan-check: **APPROVED**（带 Task 1.1/1.2 commit 粒度调整 + 新增 Wave 0 前置检查）
- assumptions: **PASS**（T3/T4/O1 已转为 Wave 0.1/0.2/5.2 显式任务）
- ready-for-build: **true**

---

## 执行前清单（Wave 0，1 次提交前完成）

- [ ] 打 tag `pre-refactor-v1.4` 作为回滚锚点（基于当前 HEAD = 356be5b）
- [x] Wave 0.1 — 已读 `scripts/convert.py`：**硬编码了 6 个 SKILL_DIRS**，其中
      `skills/intelligence` 在方案 A 后会被清空，**必须从 SKILL_DIRS 移除**；
      `skills/learning` 会保留 `continuous-learning` 一个 skill，目录保留即可。
      → 追加 Task **4.5b**：修改 `scripts/convert.py`，从 `SKILL_DIRS` 移除 `"skills/intelligence"`
- [x] Wave 0.2 — 已读 `.claude-plugin/plugin.json`：`agents` 为**显式列表**（17 项），
      `skills` 与 `commands` 为目录通配符。
      → Task 4.5 的具体改动：
        1. 在 `agents` 数组追加 `"./agents/opc-business-advisor.md"`
        2. 把 `"version": "1.0.0"` 更新为 `"1.4.0"`（当前 plugin 版本与 CHANGELOG 不同步，顺便修正）
        3. `skills` 与 `commands` 通配符保持不变

## Wave 0 追加的调整项（正式并入 Wave 4）

### Task 4.5b（新增）— convert.py SKILL_DIRS 修正

- **file**: `scripts/convert.py`
- **action**: 修改第 27-34 行 `SKILL_DIRS` 常量，移除 `"skills/intelligence"` 行
- **test-expectation**: `python scripts/convert.py --tool claude-code` 退出码 0，输出的 claude-code items 数量等于 Wave 5 之前统计的 skill+agent+command 总数
- **completion-gate**: `python scripts/convert.py --tool all` 退出码 0
- **依赖**: Wave 1.3 已完成（intelligence 目录已空）

## 参考

- `docs/archive/REFACTOR-PLAN.md` — v1.3 架构重构总体方案（前置）
- `docs/plans/2026-04-17-architecture-refactor.md` — v1.3 执行计划（前置）
- `references/plan-template.md` — 本 PLAN.md 结构规范
- `agents/opc-planner.md` — 本 PLAN.md 的 workflow 持有者
- `references/gates.md` — 门控机制
