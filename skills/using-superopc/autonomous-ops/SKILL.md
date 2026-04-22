---
name: autonomous-ops
description: Use when the user explicitly wants to enter cruise mode, check heartbeat, or perform bounded autonomous roadmap advancement. Defines GREEN/YELLOW/RED permission zones. Dispatches opc-cruise-operator, which owns cruise/heartbeat/autonomous workflows.
id: autonomous-ops
type: dispatcher
tags: [autonomous, cruise, heartbeat, zones, permission, green-yellow-red, escalation, anti-build-trap]
dispatches_to: opc-cruise-operator
triggers:
  keywords: [自主, autonomous, 权限区, cruise, 巡航, heartbeat, 心跳, 自动执行, green, yellow, red, 升级]
  phrases: ["进入巡航", "进入自主模式", "帮我自动推进", "查看心跳", "看看 cruise 状态"]
version: 1.4.2
---

# autonomous-ops — 自主运营派发器

**触发：** 用户显式进入 cruise/autonomous 模式 / 查看心跳 / 问三区权限规则。
**宣布：** "我调用 autonomous-ops 技能，派发给 opc-cruise-operator 管理自主运营。"

## 派发
使用 Task 工具派发 `opc-cruise-operator` agent。
- **输入：** cruise 模式意图 + 可选 `--mode/--hours` 边界 或 心跳查询
- **输出：** cruise_controller 生命周期转换 / heartbeat 摘要 / 有边界的自主推进循环

## 三个子场景
| 场景 | 用户表达 | 输出 |
|---|---|---|
| Cruise start | "进入巡航" / "启动 cruise" | cruise_controller 启动 + 审计日志 |
| Heartbeat | "看看心跳" / "cruise 状态" | 只读 status.json 摘要 |
| Autonomous advance | "自动推进路线图" / "从 P1 跑到 P3" | 有边界循环派发下游 skill |

## 三区权限模型（由 agent 强制执行）

### GREEN 区（自主 — 无需审批）
- 健康检查、测试执行、文档生成、情报采集、代码格式化、状态报告、seed/backlog 管理

### YELLOW 区（确认后执行）
- 代码变更、依赖升级、阶段推进、创建 PR、规划、调试循环、会话操作
- CRUISE 模式下自动执行并记录；ASSIST 模式下暂停等待确认

### RED 区（始终需要人工确认）
- 生产部署、数据库迁移、安全配置、支付/计费、破坏性操作、外部 API 密钥变更

## 升级协议（agent 强制执行）
1. GREEN → 直接执行；RED → 停并通知
2. YELLOW + cruise → 执行并记录；YELLOW + assist → 暂停等待
3. confidence < 0.5 → 无论哪一区都升级
4. 连续失败 3 次 → 切到 assist + 通知
5. 检测到 blocker → 立即暂停 + 发 `autonomous.blocked` 事件

## Anti-Build-Trap 硬门
进入 cruise / autonomous 真执行前必须确认：
1. `validate-idea` 已对本阶段形成记录？
2. `find-community` 或等价付费意愿证据存在？
3. 两者都缺 → **拒绝进入**，建议先走 `business-advisory` skill

## 集成点（仅声明，不实现）
- Decision Engine 使用本 skill 的 zone 映射做每次决策
- Cruise Controller 使用升级协议做运行时行为
- DAG Engine 在派发任务前检查 zone
- Event Bus 发 `autonomous.proceed` / `autonomous.blocked` 事件

## 监控
- 决策日志：`.opc/decisions/`
- 执行日志：`.opc/execution-log/`
- 事件日志：`.opc/events/`
- 通知队列：`.opc/notifications/`
- 所有日志人类可读（JSON + Markdown）且 git-trackable

## 边界
- 本 skill **不执行** workflow；workflow 唯一事实源是 `agents/opc-cruise-operator.md`
- 三区权限、升级协议、Anti-Build-Trap 三条规则在本文件是简要索引，完整语义在 agent + decision_engine + cruise_controller 中
