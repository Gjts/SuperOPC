# 示例 1：用 SuperOPC 构建 SaaS MVP

> 完整演示从零到上线的 SaaS 产品开发工作流

## 场景

你有一个 SaaS 产品想法：**QuickInvoice** — 帮助自由职业者 5 分钟内创建和发送专业发票。

## 工作流演示

### 第一步：初始化项目

```
/opc-start
```

SuperOPC 会引导你回答以下问题：
- 项目名称和描述
- 选择项目模板（选择 `saas-starter`）
- 确认技术栈和约束

生成的 `.opc/` 结构：

```
.opc/
  PROJECT.md          # QuickInvoice 项目定义
  REQUIREMENTS.md     # 发票 SaaS 的需求清单
  ROADMAP.md          # 5 阶段路线图
  STATE.md            # 当前状态
  config.json         # 工作流配置
```

### 第二步：市场研究（可选）

```
/opc-research run --query "自由职业者发票工具市场"
```

SuperOPC 会运行 feed → insights → methodology pipeline：
1. 分析竞品（FreshBooks, Wave, Bonsai）
2. 识别市场缺口
3. 生成 `.opc/research/YYYY-MM-DD-freelancer-invoicing-tools.md`

### 第三步：规划第一个功能

```
/opc-plan 用户认证系统（邮箱+密码+Google OAuth）
```

SuperOPC 的 `opc-planner` 代理会：
1. 设计 2-3 个方案（Supabase Auth / NextAuth / 自建）
2. 你选择方案后，生成详细的 PLAN.md
3. `opc-plan-checker` 验证计划的 8 个维度

### 第四步：执行开发

```
/opc-build
```

SuperOPC 的 `opc-executor` 代理会：
1. 按照 TDD 流程逐任务执行
2. 每个任务：先写测试 → 最小实现 → 重构
3. 完成后 `opc-reviewer` 进行五维度审查
4. 原子提交到 Git

### 第五步：查看进度

```
/opc-dashboard       # 纯只读 CLI，项目仪表盘
/opc-progress        # 派发 session-management skill → opc-session-manager 的 progress 子场景
```

`/opc-dashboard` 输出示例：
```
╔══════════════════════════════════════╗
║         QuickInvoice Dashboard      ║
╠══════════════════════════════════════╣
║ 阶段: 1/5 认证系统                    ║
║ 计划: 2/3 完成                        ║
║ 需求: 5/18 已覆盖                     ║
║ 验证欠债: 0                           ║
║ 下一步: 完成 OAuth 集成                ║
╚══════════════════════════════════════╝
```

`/opc-progress` 输出**五段式摘要 + 唯一一个推荐下一步**（agent 强制收敛，不给三选一）。

### 第六步：暂停和恢复

当天结束时：
```
/opc-pause --note "OAuth 回调 URL 需要确认"
```

`/opc-pause` 派发 `session-management` skill → `opc-session-manager`，写入 `.opc/HANDOFF.json` 并更新 `STATE.md` 连续性字段。

第二天恢复：
```
/opc-resume
```

`/opc-resume` 读 handoff → 校验 recovery_files → 对齐 STATE.md → 推荐**一个**主下一步。

> v1.4.2 前的旧用法 `python scripts/opc_pause.py` / `opc_resume.py` 已不再推荐。CLI 仍可跑，但会跳过 agent workflow 层，失去 HARD-GATE 和 validation debt 跟踪。

### 第七步：发布

```
/opc-ship
```

派发 `shipping` skill → `opc-shipper`。SuperOPC 会：
1. 运行所有测试
2. 生成变更日志
3. 创建 PR 或直接合并
4. 更新 `.opc/STATE.md`

## 关键引用与技能使用

v1.4 起技术栈与商业知识下沉到 `references/`，由 agent workflow 按需引用，不再是顶层 skill。

| 引用 / 技能 | 类型 | 使用场景 |
|-------------|------|---------|
| `references/patterns/engineering/nextjs.md` | reference | Server Components + Server Actions 架构（由 opc-executor 引用） |
| `references/patterns/engineering/postgres.md` | reference | Supabase RLS 和查询优化 |
| `references/patterns/engineering/api-design.md` | reference | RESTful 端点设计 |
| `references/business/pricing.md` | reference | 定价策略（由 opc-business-advisor 或 opc-pricing-analyst 引用） |
| `references/business/seo.md` | reference | Landing page SEO（由 opc-seo-specialist 引用） |
| `tdd` | 原子 skill | 每个功能先写测试（RED-GREEN-REFACTOR） |
| `security-review` | 派发器 skill → opc-security-auditor | 上线前 OWASP Top 10 审计 |
| `verification-loop` | 原子 skill | 4 层验证 + Nyquist 采样 |

## 代理协作流程（v1.4.2）

```
用户需求
  ↓ /opc-plan
  → opc-planner (Phase 0-5 完整流程：澄清 → 方案 → 分解 → 波次 → 检查 → pre-flight gate)
  → opc-plan-checker (8 维度验证)
  ↓ /opc-build
  → opc-executor (TDD 执行 + 子代理派发 + 原子提交)
  → opc-reviewer (五维度审查，Quick/Standard/Deep)
  ↓ /opc-security (上线前)
  → opc-security-auditor (OWASP Top 10)
  ↓ /opc-ship
  → opc-shipper (测试验证 → PR/合并 → worktree 清理)
```

跨会话与长时间推进：
- `/opc-pause` → opc-session-manager 写 HANDOFF.json
- `/opc-resume` → opc-session-manager 重建上下文
- `/opc-cruise --mode assist --hours 2` → opc-cruise-operator 启动有边界自主运营

## 预期时间线

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 认证系统 | 3-4 天 |
| 2 | 核心功能（发票 CRUD） | 5-7 天 |
| 3 | 支付集成 | 3-4 天 |
| 4 | Landing page + SEO | 2-3 天 |
| 5 | 上线准备 | 1-2 天 |
| **总计** | | **14-20 天** |
