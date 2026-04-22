---
name: session-management
description: Use when pausing, resuming, checkpointing, summarizing progress, or generating a session report for a SuperOPC project. Dispatches opc-session-manager, which owns the four sub-scenarios (pause / resume / progress / session-report).
id: session-management
type: dispatcher
tags: [session, handoff, resume, pause, checkpoint, progress, session-report, recovery]
dispatches_to: opc-session-manager
triggers:
  keywords: [暂停, 恢复, handoff, checkpoint, 继续上次, 上次到哪里, resume, pause, session, progress, 进度, 会话报告, session report]
  phrases: ["继续上次", "从哪里开始", "恢复上下文", "暂停工作", "现在进度", "生成会话报告"]
version: 1.4.2
---

# session-management — 会话连续性派发器

**触发：** 暂停 / 恢复 / 查看进度 / 生成会话报告；跨会话上下文传递相关。
**宣布：** "我调用 session-management 技能，派发给 opc-session-manager 管理会话连续性。"

## 派发
使用 Task 工具派发 `opc-session-manager` agent。
- **输入：** 用户意图（pause / resume / progress / session-report）+ 当前 `.opc/` 状态
- **输出：** HANDOFF.json 更新 / 重建的上下文 / 进度摘要 / session-report.md

## 四个子场景
| 场景 | 用户表达 | 输出 |
|---|---|---|
| Pause | "暂停一下" / "先停这里" | HANDOFF.json + 更新 STATE |
| Resume | "继续上次" / "从哪里开始" | 重建当前位置 + 一个主下一步 |
| Progress | "现在进度" / "到哪了" | 五段式摘要 + 一个推荐下一步 |
| Session report | "生成会话报告" | `.opc/session-reports/*.md` |

## 核心铁律（由 agent 强制执行）
1. **STATE 优先，handoff 其次** —— 冲突以 STATE.md 最新事实为准
2. **一个主下一步** —— 不给并列三选一
3. **明确 validation debt** —— 未验证不伪装成完成
4. **一次一个子场景** —— pause 不顺手 resume

## 边界
- 本 skill **不执行** workflow；workflow 唯一事实源是 `agents/opc-session-manager.md`
- 规则摘要在本文件；完整规则在 agent 内

## 关联
- **相关 agent：** opc-session-manager（会话连续性 workflow 持有者）
- **上游命令：** `/opc-pause` / `/opc-resume` / `/opc-progress` / `/opc-session-report`
- **脚本协作：** `scripts/opc_workflow.py` 提供只读状态查询
