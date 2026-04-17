---
name: shipping
description: Use when development and review are complete. Dispatches opc-shipper agent which owns the full release workflow — test verification, 4-option presentation (merge/PR/keep/discard), one-person-company release checklist, and worktree cleanup.
---

# shipping — 发布派发器

**触发条件：** 开发完成且已通过代码审查（opc-reviewer 判决 PASS），需要进入发布流程。适用于 "发布"、"合并"、"创建 PR"、"ship it" 等场景。

**宣布：** "我调用 shipping 技能，派发给 opc-shipper 持有完整发布 workflow。"

## 派发

使用 Task 工具派发 `opc-shipper` agent：

- **输入：** 当前功能分支（自动检测）
- **输出：** 测试验证结果 + 4 选项中的一个执行结果（合并/PR/保持/丢弃）+ worktree 清理状态

## 入口契约

- **接受**：已通过 opc-reviewer 判决 PASS 的分支
- **拒绝**：reviewer 判决 NEEDS FIX 或 REJECT 时 → 回 `reviewing` skill 或 `implementing` skill 修复

## 边界

- 本 skill **不执行**测试、不做检查清单、不操作 git —— 全部由 opc-shipper 处理
- **不内联** PR body 模板或检查清单项（在 agent 内）

## 关联

- **上游：** `reviewing` skill 判决 PASS
- **相关 agent：** opc-shipper
- **相关 skill：** git-worktrees（发布后清理）
- **规则：** `rules/common/git-workflow.md`
