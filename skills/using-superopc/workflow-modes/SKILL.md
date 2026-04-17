---
name: workflow-modes
description: Use when the task is ambiguous and the key question is "which mode should I enter?" rather than "what should I do?". Dispatches opc-orchestrator agent which owns the 7-mode decision tree (autonomous/discuss/explore/fast/quick/do/next) and the full pipeline orchestration.
---

# workflow-modes — 模式路由派发器

**触发条件：** 用户请求的目标清晰度不确定，或需要决定"现在该用哪种工作方式"。适用于 `/opc` 命令以及 "该用什么流程"、"帮我决定下一步"、"不确定怎么做" 等场景。

**宣布：** "我调用 workflow-modes 技能，派发给 opc-orchestrator 选择最合适的工作模式。"

## 派发

使用 Task 工具派发 `opc-orchestrator` agent：

- **输入：** 用户的自然语言请求 + 当前 `.opc/STATE.md` 状态
- **输出：** 选定的模式名 + 进入该模式的派发动作

## 7 种模式概览

| 模式 | 一句话 |
|---|---|
| autonomous | 已知边界内连续推进路线图工作 |
| discuss | 只澄清与取舍，不执行 |
| explore | 苏格拉底式提问，先发现真正问题 |
| fast | 一个明确微任务，直接行内完成 |
| quick | 1-3 个任务的小流程 |
| do | 自然语言意图路由到现有命令 |
| next | 基于当前状态推荐下一动作 |

**完整决策树在 `opc-orchestrator.md` 的"职责 A：模式选择决策树"。**

## 边界

- 本 skill **不做**决策 —— 决策树在 agent 内
- **不内联** 7 模式细则 —— 在 agent 内

## 关联

- **相关 agent：** opc-orchestrator（模式路由器 + 流水线编排器）
- **下游 skill：** planning / implementing / reviewing / shipping（模式选定后派发）
