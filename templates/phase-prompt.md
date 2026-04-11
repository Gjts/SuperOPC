# 阶段执行计划模板

> 用于 `.opc/phases/XX-name/{phase}-{plan}-PLAN.md` — 可执行的阶段计划，优化为并行执行。

---

## 文件模板

```markdown
---
phase: XX-name
plan: NN
type: execute
wave: N                     # 执行波次（1, 2, 3...），规划时预计算
depends_on: []              # 此计划依赖的计划 ID（如 ["01-01"]）
files_modified: []          # 此计划修改的文件
autonomous: true            # 如果计划有需要用户交互的检查点则为 false
requirements: []            # 必需 — 此计划涉及的需求 ID
checkpoints: []             # 可选 — 记录 checkpoint:decision / checkpoint:human-verify 摘要

# 目标反向验证（规划时推导，执行后验证）
must_haves:
  truths: []                # 目标达成必须为真的可观察行为
  artifacts: []             # 必须存在且有真实实现的文件
  key_links: []             # 工件之间的关键连接
---

<objective>
[此计划完成什么]

目的：[为什么这对项目重要]
输出：[将创建什么工件]
</objective>

<context>
@.opc/PROJECT.md
@.opc/ROADMAP.md
@.opc/STATE.md

[相关源文件：]
@src/path/to/relevant.ts
</context>

<tasks>

<task type="auto">
  <name>任务 1：[面向行动的名称]</name>
  <files>path/to/file.ext, another/file.ext</files>
  <read_first>path/to/reference.ext</read_first>
  <action>[具体实现 — 做什么、怎么做、避免什么以及为什么。
  包含具体值：精确标识符、参数、预期输出、文件路径。]</action>
  <verify>[证明它工作的命令或检查]</verify>
  <acceptance_criteria>
    - [可 grep 验证的条件："file.ext 包含 'exact string'"]
    - [可测量的条件："output.ext 使用 'expected-value'"]
  </acceptance_criteria>
  <done>[可测量的验收标准]</done>
</task>

<task type="auto">
  <name>任务 2：[面向行动的名称]</name>
  <files>path/to/file.ext</files>
  <action>[具体实现，包含具体值]</action>
  <verify>[命令或检查]</verify>
  <done>[验收标准]</done>
</task>

<task type="checkpoint:decision" gate="blocking">
  <decision>[需要决定什么]</decision>
  <context>[为什么这个决定重要]</context>
  <options>
    <option id="option-a"><name>[名称]</name><pros>[优势]</pros><cons>[权衡]</cons></option>
    <option id="option-b"><name>[名称]</name><pros>[优势]</pros><cons>[权衡]</cons></option>
  </options>
  <resume-signal>选择：option-a 或 option-b</resume-signal>
</task>

</tasks>

<verification>
执行后验证 must_haves：
1. truths: [逐条检查可观察行为]
2. artifacts: [确认文件存在且非空]
3. key_links: [验证工件间连接]
4. regression: [说明会影响哪些前序阶段/既有路径]
5. traceability: [标记需求 ID、测试证据、人工验证或外部来源]
</verification>
```

---

## 使用指南

### 任务类型
- **auto**：完全自动执行，无需用户干预
- **checkpoint:decision**：需要用户做出选择
- **checkpoint:human-verify**：需要用户手动验证（如 UI 检查）
- `checkpoints` frontmatter 只记录会真正阻断自动推进的检查点摘要，供 `/opc-autonomous` 与 `/opc-health` 读取

### 波次分配
- `wave: 1` — 无依赖，第一波并行执行
- `wave: 2` — 依赖 wave 1 的产物
- 同波次内的计划并行执行

### acceptance_criteria
- 必须是机器可验证的（grep、命令输出）
- 避免主观标准（"代码质量好"）
- 每个任务至少一个验收标准
