---
name: opc-review
description: Trigger a 5-dimension code review — dispatches reviewing skill which owns the workflow
---

# /opc-review — 审查入口

用户显式触发代码审查。等价于自然语言 "审查一下"。

## 动作

调用 `reviewing` skill，传入 `$ARGUMENTS`（可选的审查范围）。

reviewing skill 会派发 `opc-reviewer` agent 按 `references/review-rubric.md` 执行五维度审查。

## 参数

- `$ARGUMENTS` — 可选，指定审查范围（文件、分支、或基础分支如 `main`）；缺省时审查 `git diff main`
