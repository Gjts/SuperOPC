# SuperOPC 命令一页纸（v1.4.2）

**目的：** 用户面对 25 个 slash 命令时，30 秒内决定"我该用哪个"。

> 背后契约：命令 → dispatcher skill → agent。完整契约见 `AGENTS.md` §架构契约；Python 脚本调用规则见 §Read-only CLI 白名单例外。

---

## 🎯 3 秒决策树（从意图反查命令）

```
我想...

├── 启动一个新项目                        → /opc-start <项目名或想法>
├── 规划一个功能/阶段                     → /opc-plan <功能描述>
├── 执行已规划好的 PLAN.md                → /opc-build
├── 审查最近的代码变更                    → /opc-review
├── 发布/合并/开 PR                       → /opc-ship
│
├── 有 bug / 测试失败 / 异常排查          → /opc-debug <错误信息>
├── 上线前安全扫描                        → /opc-security <范围>
│
├── 商业决策（定价/验证/获客/营销/...）   → /opc-business <问题>
├── 新想法先验证再决定是否做              → /opc-business 验证 <想法>
│
├── 不确定该走哪条路径                    → /opc <自然语言>
│
├── 暂停工作（写 HANDOFF.json）           → /opc-pause --note "..."
├── 恢复上次工作                          → /opc-resume
├── 查看当前进度                          → /opc-progress
├── 生成会话报告                          → /opc-session-report
│
├── 启动自主巡航（有边界）                → /opc-cruise --mode assist --hours 2
├── 查看巡航心跳                          → /opc-heartbeat
├── 在路线图窗口内自动推进                → /opc-autonomous --from 2 --to 4
│
├── 查看项目仪表盘（只读）                → /opc-dashboard
├── 查看结构化指标（JSON）                → /opc-stats
├── 跑项目健康检查                        → /opc-health [--repair]
├── 查询代码库情报                        → /opc-intel query <term>
├── 查看开发者画像                        → /opc-profile
├── 查看研究产物索引                      → /opc-research
│
├── 快速记一条跨会话上下文                → /opc-thread <名称>
├── 快速记一个未来想法（种子）            → /opc-seed <想法>
└── 快速记一条延后待办                    → /opc-backlog <事项>
```

---

## 🚀 端到端标准旅程

**从"有一个想法"到"上线 MRR"**：

```
          ┌─────────────────────────────────────────┐
          │  Day 0: 商业验证                         │
          │                                         │
  /opc-business 我想做个自由职业者发票 SaaS         │
          │  ↓                                       │
          │  opc-business-advisor (validate-idea) → │
          │  用户访谈 + 付费意愿证据                 │
          │                                         │
          └─────────────────────────────────────────┘
                          ↓ 证据充分
          ┌─────────────────────────────────────────┐
          │  Day 1: 初始化                           │
          │                                         │
  /opc-start QuickInvoice 自由职业者发票 SaaS       │
          │  ↓                                       │
          │  opc-orchestrator → 创建 .opc/PROJECT   │
          │  .md / ROADMAP.md / STATE.md            │
          │                                         │
          └─────────────────────────────────────────┘
                          ↓ 脚手架就绪
          ┌─────────────────────────────────────────┐
          │  Day 2-3: 第一个功能                     │
          │                                         │
  /opc-plan 用户认证 (邮箱 + Google OAuth)          │
          │  ↓                                       │
          │  opc-planner Phase 0-5 →                │
          │  opc-plan-checker 8 维度验证 →          │
          │  PLAN.md (ready-for-build: true)        │
          │                                         │
  /opc-build                                        │
          │  ↓                                       │
          │  opc-executor TDD + 波次 →              │
          │  opc-reviewer 五维度审查 →              │
          │  原子提交 + SUMMARY.md                  │
          │                                         │
          └─────────────────────────────────────────┘
                          ↓ 功能完成
          ┌─────────────────────────────────────────┐
          │  Day 3 晚: 暂停                          │
          │                                         │
  /opc-pause --note "OAuth 回调 URL 待确认"         │
          │  ↓                                       │
          │  opc-session-manager 写 HANDOFF.json    │
          │  commit .opc/ → push                    │
          │                                         │
          └─────────────────────────────────────────┘
                          ↓ 明天
          ┌─────────────────────────────────────────┐
          │  Day 4 早: 恢复                          │
          │                                         │
  git pull                                          │
  /opc-resume                                       │
          │  ↓                                       │
          │  opc-session-manager → 重建上下文 →     │
          │  推荐一个主下一步                        │
          │                                         │
          └─────────────────────────────────────────┘
                          ↓ 更多功能迭代...
          ┌─────────────────────────────────────────┐
          │  Day N: 上线前                           │
          │                                         │
  /opc-security app/api/                            │
          │  ↓ OWASP Top 10 审计                    │
  /opc-review                                       │
          │  ↓ 五维度全局审查                       │
  /opc-ship                                         │
          │  ↓                                       │
          │  opc-shipper → 测试 → PR/合并 →         │
          │  worktree 清理                          │
          │                                         │
          └─────────────────────────────────────────┘
                          ↓ 上线后
          ┌─────────────────────────────────────────┐
          │  持续运营                                 │
          │                                         │
  /opc-cruise --mode assist --hours 4               │
          │  ↓ 有边界自主运营                        │
  /opc-heartbeat              # 查看巡航状态         │
  /opc-dashboard              # 查看业务指标         │
  /opc-business 定价调整       # 业务决策咨询       │
          │                                         │
          └─────────────────────────────────────────┘
```

---

## 🚨 硬门与错误路径速查

| 错误 | 原因 | 修复 |
|------|------|------|
| `/opc-plan` 被拒 "validate-idea 缺失" | Anti-Build-Trap 硬门触发 | `/opc-business 验证 <想法>` 走 validate-idea 子活动，完成后重试 |
| `/opc-build` 报 "ready-for-build: false" | opc-plan-checker 验证未通过 | 读 PLAN.md 末尾"修订意见" → 手工修或 `/opc-plan --revise` |
| `/opc-build` 遇测试失败 | 实现与测试不符 | opc-executor 自动派发 opc-debugger；3 次失败 → 升级到用户 |
| `/opc-cruise` 被拒 "边界未指定" | cruise 必须有时限 | 加 `--hours N` 或 `--mode watch` |
| `/opc-cruise` 被拒 "Anti-Build-Trap" | 窗口内有未验证商业阶段 | 先 `/opc-business` 验证 |
| `/opc-resume` 报 "HANDOFF.json 不存在" | 上次没 pause 或文件被误删 | 自动回退读 STATE.md；若也缺失 → `/opc-start` |
| `/opc-resume` 报 "recovery_files 失效" | 文件被删/重命名/跨机路径不同 | opc-session-manager 列出冲突项；逐条确认跳过或手动修复 |
| `/opc-ship` 测试失败 | 发布前测试回归 | opc-shipper 暂停；`/opc-debug` 修复后重试 |

---

## 📋 权限区速查（cruise 模式）

| 动作类别 | GREEN 区 | YELLOW 区 | RED 区 |
|----------|----------|-----------|--------|
| **watch 模式** | ❌ 不执行 | ❌ 不执行 | ❌ 不执行 |
| **assist 模式** | ✅ 自动执行 | ⏸️ 暂停等待人工确认 | 🚨 notification + 等待 |
| **cruise 模式** | ✅ 自动执行 | ✅ 自动执行 | 🚨 notification + 等待 |

- **GREEN**：健康检查、测试执行、文档生成、情报查询、状态报告、代码格式化
- **YELLOW**：代码变更、依赖升级、阶段推进、PR 创建、规划、调试
- **RED**：生产部署、DB migration、支付配置、安全敏感变更、破坏性操作、外部 API 密钥

详细定义见 `skills/using-superopc/autonomous-ops/SKILL.md`。

---

## 🔧 只读 vs 写入 CLI 白名单（v1.4.2 分两档）

| 档 | 命令 | 是否允许直接 `python scripts/xxx.py` |
|----|------|-------------------------------------|
| **PURE 只读** | `/opc-health` `/opc-dashboard` `/opc-stats` `/opc-intel` `/opc-profile` `/opc-research` | ✅ 是（无副作用） |
| **MIXED 低摩擦** | `/opc-thread` `/opc-seed` `/opc-backlog` | ⚠️ 是（但创建模式会写 `.opc/`，stderr 输出 advisory） |
| **派发器命令** | 其他 16 个（plan/build/review/ship/debug/security/business/pause/resume/progress/...） | ❌ 否（必须走 slash 命令派发 skill） |

`scripts/verify_command_contract.py` 在 CI 强制这套规则。

---

**一页纸维护原则：** 本文件只描述**已落地**的命令与契约。新增命令或契约变更 → 先更新 `AGENTS.md` + `commands/opc/*.md` + lint，通过后再回流到本文件。
