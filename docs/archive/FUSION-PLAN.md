# SuperOPC 融合蓝图 — 九大来源项目深度融合计划

> Historical archive: this document captures the pre-v1.4 fusion plan and old repo counts. It is kept for project history only. Current source of truth lives in `README.md`, `AGENTS.md`, and `docs/DIRECTORY-MAP.md`.

> 生成时间: 2026-04-12 | 当前版本: v1.0.0 | 目标: v2.0.0

---

## 一、融合现状总览

### SuperOPC v1.0.0 资产清单

| 资产类型 | 数量 | 位置 |
|---------|------|------|
| 技能 (Skills) | 47 | `skills/` (business/19, engineering/19, intelligence/3, learning/3, product/5+) |
| 代理 (Agents) | 18 | `agents/` (core/15, matrix/3) |
| 命令 (Commands) | 27 | `commands/opc/` |
| 引用 (References) | 11 | `references/` |
| 规则 (Rules) | 17 | `rules/` (common/5, ts/3, cs/3, py/3, kt/3) |
| 钩子 (Hooks) | 11 | `hooks/hooks.json` + `scripts/hooks/` |
| 引擎模块 (Engine) | 10 | `scripts/engine/` |
| 模板 (Templates) | 15 | `templates/` |
| 项目模板 | 4 | `templates/projects/` |

---

## 二、九大来源项目能力矩阵

### 1. Superpowers — AI 代理开发工作流系统

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 技能优先规则 (skill-first) | ✅ CLAUDE.md 行为协议 #1 | — | — |
| TDD 铁律 (iron law) | ✅ tdd/SKILL.md + rules/common/testing.md | — | — |
| 头脑风暴门控 (hard gate) | ✅ brainstorming/SKILL.md | — | — |
| 子代理驱动开发 (subagent-driven) | ⚠️ parallel-agents 部分覆盖 | 双阶段审查(spec+quality)、实现者/审查者提示模板 | 🔴 高 |
| Git Worktree 隔离 | ✅ git-worktrees/SKILL.md | — | — |
| 分支完成工作流 | ✅ ship 命令覆盖 | — | — |
| 技能创建 TDD (writing-skills) | ✅ writing-skills/SKILL.md | CSO 描述陷阱发现、反合理化表格模板 | 🟡 中 |
| 系统化调试 4 阶段 | ✅ debugging/SKILL.md + opc-debugger | — | — |
| 计划编写技能 | ✅ planning/SKILL.md | — | — |

**融合差距**: 子代理驱动开发的**双阶段审查协议**尚未完整融合——缺少 `implementer-prompt.md`、`spec-reviewer-prompt.md`、`code-quality-reviewer-prompt.md` 三个子代理提示模板。

### 2. GSD — 命令到执行的完整追踪系统

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 项目初始化 (new-project) | ✅ /opc-start | — | — |
| 阶段规划 (plan-phase) | ✅ /opc-plan | — | — |
| 波次执行 (execute-phase) | ✅ /opc-build + parallel-agents | — | — |
| 目标反向验证 (verify-work) | ✅ /opc-review + verification-loop | — | — |
| 快速任务 (quick) | ✅ /opc-quick + /opc-fast | — | — |
| 会话管理 (pause/resume/progress) | ✅ v0.8 完整实现 | — | — |
| 自主执行 (autonomous) | ✅ /opc-autonomous + cruise_controller | — | — |
| 开发者画像 (8维度 profiling) | ⚠️ profile_engine.py 骨架 | 问卷生成、USER-PROFILE.md 输出、CLAUDE.md 注入 | 🔴 高 |
| 全局学习存储 | ⚠️ learning_store.py 骨架 | 跨项目洞察持久化、计划器注入 | 🔴 高 |
| 可查询代码库智能 (intel) | ⚠️ /opc-intel 命令存在 | JSON索引生成(stack/api-map/dependency-graph) | 🟡 中 |
| CLI 工具层 (gsd-tools 19模块) | ❌ | bin/opc-tools 完整CLI | 🟡 中 |
| 安全强化 | ⚠️ 基础注入检测 | Unicode不可见字符、编码混淆、熵分析 | 🟡 中 |
| 持久调试会话 | ⚠️ debug.md 模板 | 假设追踪持久化、knowledge-base.md | 🟡 中 |
| 取证分析 (forensics) | ❌ | Git历史异常检测、工件完整性报告 | 🟢 低 |
| 安全撤销 (undo) | ❌ | 依赖检查+硬确认门 | 🟢 低 |
| 跨AI同行评审 | ❌ | 多模型审查、REVIEWS.md | 🟢 低 |
| 工作流引擎 (68工作流) | ❌ | workflows/ 目录、薄编排器 | 🟡 中 |
| 里程碑管理 | ❌ | audit/complete/new milestone | 🟡 中 |
| 工作流命名空间 | ❌ | 并行工作流隔离 | 🟢 低 |
| SDK | ❌ | TypeScript SDK | 🟢 低 |

### 3. ECC — 核心系统执行流程

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 安装系统 | ⚠️ convert.py 覆盖导出 | 交互式安装器 (npx superopc) | 🟢 低 |
| 钩子系统 (hooks.json) | ✅ 完整移植 | — | — |
| 持续学习 v2 | ⚠️ learning_store.py 骨架 | 观察钩子→JSONL→本能聚类→技能演化 | 🔴 高 |
| 代理委托 (code-reviewer等) | ✅ 15+代理 | — | — |
| TDD 工作流技能 | ✅ tdd/SKILL.md | — | — |
| MCP 集成 | ✅ mcp-configs/ | — | — |
| Rules 12语言 | ⚠️ 4语言(ts/cs/py/kt) | golang/rust/java/swift/dart/php/cpp/ruby | 🟢 低 |
| 项目作用域本能 | ❌ | 按git remote hash隔离项目学习 | 🟡 中 |

### 4. Agency-Agents — 144+ 专业代理库

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 代理标准结构 | ✅ 参考了frontmatter+Identity+Mission+Rules格式 | — | — |
| 工程代理 (26个) | ⚠️ 3个matrix代理 | backend-architect扩展、devops、ai-engineer等 | 🟡 中 |
| 营销代理 (29个) | ❌ | seo-specialist、content-creator、growth-hacker等 | 🟡 中 |
| 策略代理 | ❌ | strategy-nexus、product-manager | 🟡 中 |
| 代理路由器 | ✅ registry.json + dag_engine语义匹配 | — | — |
| 多工具转换 (convert.sh) | ✅ convert.py 覆盖11运行时 | — | — |
| 协调器 (AgentsOrchestrator) | ✅ opc-orchestrator | — | — |

### 5. Minimalist Entrepreneur Skills

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 10个商业技能 | ✅ skills/business/ 完整 | — | — |
| Anti-Build-Trap 守卫 | ✅ CLAUDE.md 行为协议 #4 | — | — |

### 6. Follow Builders

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 构建者追踪技能 | ✅ follow-builders/SKILL.md | — | — |
| BUILDER-INTEL 协议 | ✅ CLAUDE.md 行为协议 #8 | — | — |
| 多源聚合引擎 | ⚠️ 基础技能 | 定时聚合+推送+摘要生成 | 🟢 低 |

### 7. Skill From Masters

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 案例驱动技能创建 | ✅ skill-from-masters/SKILL.md | — | — |
| METHODOLOGY-FIRST 协议 | ✅ CLAUDE.md 行为协议 #9 | — | — |
| 方法论数据库 | ❌ | references/methodology-database.md | 🟡 中 |
| 技能分类法 | ❌ | references/skill-taxonomy.md | 🟡 中 |

### 8. last30days

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 多源社交媒体研究 | ✅ market-research/SKILL.md | — | — |
| MULTI-SOURCE 协议 | ✅ CLAUDE.md 行为协议 #10 | — | — |

### 9. Claude Code Best Practice

| 核心能力 | 已融合 | 未融合 | 优先级 |
|---------|--------|--------|--------|
| 编排工作流模式 | ✅ AGENTS.md + dag_engine | — | — |
| 原子提交 | ✅ CLAUDE.md 行为协议 #11 | — | — |
| 钩子系统最佳实践 | ✅ hooks/ | — | — |

---

## 三、未融合能力优先级排序

### 🔴 P0 — 立即实施 (v1.1.0)

| # | 能力 | 来源 | 预计文件数 | 复杂度 |
|---|------|------|-----------|--------|
| 1 | **子代理双阶段审查协议** | Superpowers | 4 | 高 |
| 2 | **开发者画像完整实现** | GSD | 3 | 高 |
| 3 | **全局学习存储完整实现** | GSD+ECC | 4 | 高 |
| 4 | **持续学习观察管道** | ECC | 3 | 高 |

### 🟡 P1 — 近期实施 (v1.2-v1.4)

| # | 能力 | 来源 | 预计文件数 | 复杂度 |
|---|------|------|-----------|--------|
| 5 | 代码库智能索引 | GSD | 3 | 中 |
| 6 | 方法论数据库+技能分类法 | skill-from-masters | 2 | 低 |
| 7 | 领域代理精选(工程+营销+策略) | Agency-Agents | 15+ | 中 |
| 8 | CLI工具层 | GSD | 5 | 高 |
| 9 | 安全强化(Unicode/编码/熵) | GSD | 2 | 中 |
| 10 | 工作流引擎目录 | GSD | 10 | 高 |
| 11 | 里程碑管理 | GSD | 3 | 中 |
| 12 | 持久调试会话 | GSD | 2 | 中 |

### 🟢 P2 — 远期实施 (v1.5-v2.0)

| # | 能力 | 来源 | 预计文件数 |
|---|------|------|-----------|
| 13 | 取证分析 | GSD | 2 |
| 14 | 安全撤销 | GSD | 2 |
| 15 | 跨AI同行评审 | GSD | 3 |
| 16 | 工作流命名空间 | GSD | 3 |
| 17 | TypeScript SDK | GSD | 10 |
| 18 | 交互式安装器 | ECC | 3 |
| 19 | 多源聚合推送 | Follow Builders | 2 |
| 20 | 更多语言Rules | ECC | 16 |

---

## 四、v1.1.0 实施方案 — 子代理审查 + 画像 + 学习

### 4.1 子代理双阶段审查协议 (来源: Superpowers)

**目标**: 将 Superpowers 的 subagent-driven-development 完整融合到 SuperOPC

**新增文件**:
- `skills/engineering/subagent-driven-development/SKILL.md` — 主技能
- `skills/engineering/subagent-driven-development/implementer-prompt.md` — 实现者子代理模板
- `skills/engineering/subagent-driven-development/spec-reviewer-prompt.md` — 规格审查模板
- `skills/engineering/subagent-driven-development/code-quality-reviewer-prompt.md` — 代码质量审查模板

**修改文件**:
- `skills/engineering/parallel-agents/SKILL.md` — 添加对 subagent-driven-development 的引用
- `AGENTS.md` — 添加子代理审查流水线

**核心流程**:
```
计划 → 提取任务 → [每任务: 派发实现者 → 规格审查 → 代码质量审查 → 标记完成] → 最终审查 → 分支完成
```

### 4.2 开发者画像完整实现 (来源: GSD)

**目标**: 让 profile_engine.py 从骨架变为可用

**新增文件**:
- `commands/opc/profile.md` — 已存在，需充实
- `templates/user-profile.md` — 画像输出模板
- `skills/using-superopc/developer-profile/SKILL.md` — 画像技能

**增强文件**:
- `scripts/engine/profile_engine.py` — 实现问卷生成、8维度评估、CLAUDE.md注入

**8维度**:
1. 沟通风格 (简洁/详细)
2. 决策模式 (数据驱动/直觉)
3. 调试方式 (系统化/探索式)
4. UX 偏好 (功能优先/美学优先)
5. 技术选择 (保守/前沿)
6. 摩擦触发 (冗长输出/缺少上下文)
7. 学习风格 (示例/原理)
8. 解释深度 (最小/全面)

### 4.3 全局学习存储 + 持续学习管道 (来源: GSD + ECC)

**目标**: 实现 观察→聚类→本能→技能演化 的完整管道

**新增文件**:
- `scripts/hooks/observe.py` — 工具使用观察钩子
- `skills/learning/continuous-learning/observe-hook.md` — 观察钩子文档

**增强文件**:
- `scripts/engine/learning_store.py` — 实现 JSONL 观察写入、模式检测、本能生成
- `hooks/hooks.json` — 注册观察钩子

**数据流**:
```
工具调用 → observe.py (捕获元数据) → ~/.opc/learnings/observations.jsonl
→ learning_store.py (模式分析) → ~/.opc/learnings/instincts/*.yaml
→ context_assembler.py (注入相关本能到会话)
```

---

## 五、融合设计原则

1. **重新设计，不是复制** — 不直接复制来源文件，而是重新设计以保持 OPC 视角一致性
2. **一人公司优先** — 每个融合决策都从「一人公司创始人需要什么」出发
3. **技能驱动** — 所有新能力首先表达为技能，然后才是命令和代理
4. **渐进增强** — 引擎模块从骨架→可用→优化三阶段演进
5. **11协议守护** — CLAUDE.md 中的11条行为协议是融合的质量红线

---

## 六、来源项目融合完成度

| 来源项目 | 总能力 | 已融合 | 未融合 | 完成度 |
|---------|--------|--------|--------|--------|
| Superpowers | 9 | 7 | 2 | 78% |
| GSD | 20 | 8 | 12 | 40% |
| ECC | 8 | 5 | 3 | 63% |
| Agency-Agents | 6 | 4 | 2 | 67% |
| Minimalist Entrepreneur | 2 | 2 | 0 | 100% |
| Follow Builders | 3 | 2 | 1 | 67% |
| Skill From Masters | 3 | 1 | 2 | 33% |
| last30days | 2 | 2 | 0 | 100% |
| Claude Code Best Practice | 3 | 3 | 0 | 100% |
| **总计** | **56** | **34** | **22** | **61%** |
