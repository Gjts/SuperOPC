---
name: planning
description: Use after brainstorming design is approved. Breaks design into bite-sized executable tasks with exact code references, commands, and test expectations. Produces a PLAN.md file.
---

## 实施计划编写

**前提：** 设计规格已经通过 brainstorming 技能获得用户批准。

**宣布：** "我正在使用 planning 技能，将设计分解为可执行的任务列表。"

## 输出格式

将计划保存到 `docs/plans/YYYY-MM-DD-<feature-name>.md`

```markdown
# [功能名称] 实施计划

> **执行要求：** 使用 superopc:implementing 技能执行此计划。每个任务使用 TDD。

**目标：** [一句话描述构建什么]

**设计规格：** [链接到规格文档]

## 任务列表

### 任务 1: [标题]
**文件：** `path/to/file.ts`
**做什么：** [具体描述]
**测试期望：** [测试应该验证什么]
**完成标志：** [怎么知道做完了]

### 任务 2: [标题]
...
```

## 任务分解原则

1. **每个任务 2-5 分钟**：能在一个 AI 子代理上下文中完成
2. **原子性**：每个任务独立可提交
3. **依赖明确**：标注任务间的依赖关系
4. **测试驱动**：每个任务都有预期的测试
5. **具体路径**：指明要修改的确切文件和函数

## 任务结构检查清单

每个任务必须包含：
- [ ] 要修改/创建的文件路径
- [ ] 具体的修改内容描述
- [ ] 测试预期（什么应该通过/失败）
- [ ] 完成标志

## 波次优化（来自 GSD）

将独立任务分组为"波次"，同一波次内的任务可并行执行：

```markdown
## 波次 1（可并行）
- 任务 1: 创建数据模型
- 任务 2: 创建 API 路由骨架

## 波次 2（依赖波次 1）
- 任务 3: 实现 API 逻辑
- 任务 4: 实现数据验证
```

## 移交

计划完成后：
- **必须** 调用 `implementing` 技能执行计划
- 每个任务用子代理执行 + TDD
- 完成后调用 `reviewing` 技能审查
