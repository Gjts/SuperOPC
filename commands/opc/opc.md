---
name: opc
description: Natural-language entry for SuperOPC — routes intent to the right mode (autonomous/discuss/explore/fast/quick/do/next) via workflow-modes skill
---

# /opc — SuperOPC 统一入口

用户显式触发 SuperOPC，但不确定用哪种模式时使用。等价于对自然语言意图做模式路由。

**替代的旧命令（迁移映射）：**

| 旧命令 | 新路径 |
|---|---|
| `/opc-do` | `/opc` + 自然语言描述 |
| `/opc-next` | `/opc next` |
| `/opc-discuss` | `/opc discuss` + 话题 |
| `/opc-explore` | `/opc explore` + 问题 |
| `/opc-fast` | `/opc fast` + 微任务 |
| `/opc-quick` | `/opc quick` + 小任务流 |

## 动作

调用 `workflow-modes` skill，传入 `$ARGUMENTS`。

workflow-modes skill 会派发 `opc-orchestrator` agent 按 7 模式决策树选择最合适的入口。

## 参数

- `$ARGUMENTS` — 自然语言描述，可选含模式提示（如 `discuss 登录方案`、`fast 改 README 拼写`）

## 示例

- `/opc 我想做个支付系统` → orchestrator 判断需求模糊 → 进入 `explore`
- `/opc discuss 选 Stripe 还是 Paddle` → 直接进入 `discuss`
- `/opc next` → 读 `.opc/STATE.md` 推荐下一动作
