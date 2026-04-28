# Workflow Modes — 工作流模式

`workflow-modes` 是 dispatcher skill，派发 `opc-orchestrator` 持有 7 模式决策树。v1.4 起旧的 `/opc-fast`、`/opc-quick`、`/opc-discuss`、`/opc-explore`、`/opc-do`、`/opc-next` 独立入口已合并到统一 `/opc <自然语言>`。

---

## 7 种模式

| 模式 | 入口表达 | 适用场景 | 不适用场景 |
|---|---|---|---|
| `autonomous` | `/opc "autonomous: ..."` 或 `/opc-autonomous` | 范围已知、状态清楚、希望在边界内连续推进 | 需求模糊、存在 blocker、高风险决策未确认 |
| `discuss` | `/opc "discuss: ..."` | 只澄清与取舍，不执行、不写文件 | 已有明确实现计划 |
| `explore` | `/opc "explore: ..."` | 苏格拉底式探索，先发现真正问题和隐藏假设 | 用户只要一个明确小修 |
| `fast` | `/opc "fast: ..."` | 一个明确、低风险、低范围微任务 | 多文件设计、多步拆解、需要正式计划 |
| `quick` | `/opc "quick: ..."` | 1-3 个任务的小流程，比 `fast` 更完整但比 plan/build 更轻 | 需要 PLAN.md、审查门或跨模块协调 |
| `do` | `/opc "<自然语言需求>"` | 用户只说一句需求，需要路由到已有 command / skill | 已经明确指定了 `/opc-plan` 等命令 |
| `next` | `/opc "next"` | 基于当前 `.opc/STATE.md` 推荐下一步 | 用户已经给出明确要执行的动作 |

---

## 选型规则

- **问题不清楚** → `explore`
- **问题清楚但方案未定** → `discuss`
- **一个很小的明确任务** → `fast`
- **少量任务，需要轻量执行流程** → `quick`
- **范围已知，想减少逐步确认** → `autonomous`
- **需要正式规划** → `/opc-plan`
- **用户只说一句自然语言，不知道用哪个命令** → `do`
- **不知道现在下一步该做什么** → `next`

---

## 与其他入口的边界

- `/opc` 是统一自然语言入口；它只派发 `workflow-modes`，由 `opc-orchestrator` 选择模式或下游 command / skill。
- `/opc-autonomous`、`/opc-cruise`、`/opc-heartbeat` 是自主运营专用入口，走 `autonomous-ops` skill，而不是 generic `workflow-modes`。
- `/opc-thread`、`/opc-seed`、`/opc-backlog` 是 mixed low-friction CLI，用于快速捕获上下文，不触发 workflow-modes。

---

## 原则

1. 先选对模式，再进入实现。
2. 有现成命令就路由，不重复造轮子。
3. `discuss` / `explore` 不应偷偷改文件。
4. `fast` 超出一个微任务时升级到 `quick` 或 `/opc-plan`。
5. 输出尽量收敛到一个主动作。
