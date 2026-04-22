---
name: opc-start
description: Initialize a new one-person company project — dispatches workflow-modes skill to route between fresh-project init and resume-project flows
---
# /opc-start — 项目初始化入口
用户启动 SuperOPC 项目的统一入口。等价于自然语言 "开始一个新项目" / "在这个目录初始化 SuperOPC"。
## 动作
调用 `workflow-modes` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=project-init`。
workflow-modes skill 会派发 `opc-orchestrator` agent，由 orchestrator 根据当前目录状态分叉：
- **若 `.opc/` 不存在（全新项目）**：澄清项目定位、目标用户、技术栈、初始需求 → 创建 `.opc/PROJECT.md` + `ROADMAP.md` + `STATE.md` → 建议 `/opc-plan <第一个功能>`
- **若 `.opc/` 已存在（已有项目新阶段）**：读取 `STATE.md` → 摘要当前阶段与 validation debt → 建议下一步（可能是 `/opc-resume` 或 `/opc-plan <新功能>`）
- **若请求包含"新的商业想法"信号**：改派发 `business-advisory` skill 走 `validate-idea` 子活动，触发 Anti-Build-Trap HARD-GATE
## 参数
- `$ARGUMENTS` — 项目名称、想法、约束或初始化说明；orchestrator 会从中提取意图分叉
## 常见场景
- `/opc-start QuickInvoice 自由职业者发票 SaaS` → orchestrator 识别为新项目 → 派发 planning
- `/opc-start` → orchestrator 识别 `.opc/` 已存在 → 派发 session-management 的 progress 子场景
- `/opc-start 想做一个 AI 写作工具` → orchestrator 识别 fresh idea → 派发 business-advisory（validate-idea）
