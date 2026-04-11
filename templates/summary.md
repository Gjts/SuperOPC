# 阶段摘要模板

> 用于 `.opc/phases/XX-name/{phase}-{plan}-SUMMARY.md` — 阶段完成文档。

---

## 文件模板

```markdown
---
phase: XX-name
plan: YY
subsystem: [主类别：auth, payments, ui, api, database, infra, testing 等]
tags: [可搜索技术标签：jwt, stripe, react, postgres]

# 依赖图
requires:
  - phase: [依赖的前序阶段]
    provides: [该阶段构建的、本阶段使用的内容]
provides:
  - [本阶段构建/交付的内容列表]
affects: [需要此上下文的阶段名或关键词]

# 技术追踪
tech-stack:
  added: [本阶段添加的库/工具]
  patterns: [建立的架构/代码模式]

key-files:
  created: [创建的重要文件]
  modified: [修改的重要文件]

key-decisions:
  - "决策 1"
  - "决策 2"

patterns-established:
  - "模式 1：描述"

requirements-completed: []  # 必需 — 复制计划 frontmatter 中的所有需求 ID
verification-files: []      # 必需 — 指向对应的 `*-VERIFICATION.md`
claim-sources: []           # 关键结论的来源（文件、issue、URL、手动验证项）

# 指标
duration: Xmin
completed: YYYY-MM-DD
---

# 阶段 [X]：[名称] 摘要

**[描述结果的实质性一句话 — 不是"阶段完成"或"实现完成"]**

## 性能

- **耗时：** [时间]（如 23 分钟、1小时15分）
- **开始：** [ISO 时间戳]
- **完成：** [ISO 时间戳]
- **任务数：** [已完成数量]
- **修改文件数：** [数量]

## 成就
- [最重要的成果]
- [第二个关键成就]
- [第三个（如适用）]

## 提交记录

每个任务原子提交：

1. **任务 1：[名称]** - `abc123f`（feat/fix/test/refactor）
2. **任务 2：[名称]** - `def456g`（feat/fix/test/refactor）

## 创建/修改的文件
- `path/to/file.ts` - 做什么的
- `path/to/another.ts` - 做什么的

## 技术决策
- [关键决策 1：选择了什么，为什么]
- [关键决策 2：选择了什么，为什么]

## 验证记录

### Tests
- [命令] — [通过 / 失败 / 未运行]

### Manual verification
- [ ] [需要人工确认的路径或截图检查]

### Regression impact
- 影响面：[本阶段可能影响的前序功能 / 测试面]
- 新增欠债：[无 / 具体说明]

### Claims and sources
- 结论：[你声称已经完成的结论]
  - 来源：[文件路径 / issue / URL / 手动验证项]

## 下阶段准备度

### 就绪
- [✓] [后续阶段可以依赖的内容]

### 关注
- [⚠️] [需要注意的技术债或风险]

### 阻塞
- 无

## 验证结果
- **自动化测试：** [已运行什么，结果如何]
- **人工验证：** [需要/已完成的人工验证项]
- **回归影响：** [受影响的旧路径、组件或阶段]
- **Schema drift：** [无 / 已检查 / 需要补迁移]

## 声明溯源
- **需求来源：** [REQ-ID 列表]
- **代码证据：** [关键文件或提交]
- **验证证据：** [测试、截图、手动检查、外部资料]
```

---

## 使用指南

### 何时创建
- 计划中所有任务完成后
- 验证通过后
- 在状态转换之前

### frontmatter 的重要性
- `requirements-completed` 必须非空 — 与 REQUIREMENTS.md 的可追溯性关联
- `verification-files` 必须指向实际验证工件 — 供 `/opc-health` 做回归门与覆盖门检查
- `claim-sources` 用于标记关键结论的来源，避免无来源完成声明
- `provides` 和 `affects` 用于跨阶段依赖分析
- `duration` 用于性能指标追踪
