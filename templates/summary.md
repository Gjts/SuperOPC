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

## 下阶段准备度

### 就绪
- [✓] [后续阶段可以依赖的内容]

### 关注
- [⚠️] [需要注意的技术债或风险]

### 阻塞
- 无
```

---

## 使用指南

### 何时创建
- 计划中所有任务完成后
- 验证通过后
- 在状态转换之前

### frontmatter 的重要性
- `requirements-completed` 必须非空 — 与 REQUIREMENTS.md 的可追溯性关联
- `provides` 和 `affects` 用于跨阶段依赖分析
- `duration` 用于性能指标追踪
