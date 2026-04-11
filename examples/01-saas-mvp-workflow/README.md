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
/opc-research 自由职业者发票工具市场
```

SuperOPC 的 `opc-researcher` 代理会：
1. 分析竞品（FreshBooks, Wave, Bonsai）
2. 识别市场缺口
3. 生成 `.opc/research/market-analysis.md`

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

```bash
python scripts/opc_dashboard.py --cwd .
```

输出：
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

### 第六步：暂停和恢复

当天结束时：
```bash
python scripts/opc_pause.py --cwd . --note "OAuth 回调 URL 需要确认"
```

第二天恢复：
```bash
python scripts/opc_resume.py --cwd .
```

### 第七步：发布

```
/opc-ship
```

SuperOPC 会：
1. 运行所有测试
2. 生成变更日志
3. 创建 PR 或直接合并
4. 更新 `.opc/STATE.md`

## 关键技能使用

| 技能 | 使用场景 |
|------|---------|
| `nextjs-patterns` | Server Components + Server Actions 架构 |
| `postgres-patterns` | Supabase RLS 和查询优化 |
| `tdd` | 每个功能先写测试 |
| `api-design` | RESTful 端点设计 |
| `pricing` | 定价策略（Free / Pro / Enterprise） |
| `seo` | Landing page SEO 优化 |
| `security-review` | 上线前安全审计 |

## 代理协作流程

```
用户需求
  → opc-planner (规划 2-3 方案)
  → opc-plan-checker (8 维度验证)
  → opc-executor (TDD 执行)
  → opc-reviewer (五维度审查)
  → opc-verifier (目标反向验证)
  → opc-security-auditor (安全扫描)
```

## 预期时间线

| 阶段 | 内容 | 预计时间 |
|------|------|---------|
| 1 | 认证系统 | 3-4 天 |
| 2 | 核心功能（发票 CRUD） | 5-7 天 |
| 3 | 支付集成 | 3-4 天 |
| 4 | Landing page + SEO | 2-3 天 |
| 5 | 上线准备 | 1-2 天 |
| **总计** | | **14-20 天** |
