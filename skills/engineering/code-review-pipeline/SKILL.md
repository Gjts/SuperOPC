---
name: code-review-pipeline
description: Use when reviewing code changes. Three-level review depth (quick/standard/deep) with structured checklist covering correctness, security, performance, and maintainability.
---

## 代码审查流水线

**宣布：** "我正在使用 code-review-pipeline 技能进行代码审查。"

## 何时激活

- 用户请求代码审查
- PR/MR 就绪
- 阶段完成后审查
- 发布前最终检查

## 三级审查深度

### Quick（快速）— 5 分钟
```
适用：小修改、配置变更、文档更新

检查清单：
- [ ] 代码能编译/运行？
- [ ] 无明显错误？
- [ ] 命名合理？
- [ ] 无硬编码密钥？
```

### Standard（标准）— 15-30 分钟
```
适用：普通功能开发、Bug 修复

检查清单（Quick 全部 +）：
- [ ] 业务逻辑正确？
- [ ] 错误处理完整？（空值、异常、边界）
- [ ] 输入验证？
- [ ] SQL 参数化？（无注入风险）
- [ ] 测试覆盖？（新功能有测试？）
- [ ] 性能问题？（N+1、大循环、无索引查询）
- [ ] 一致性？（遵循项目约定？）
```

### Deep（深度）— 1-2 小时
```
适用：核心架构变更、安全关键功能、支付逻辑

检查清单（Standard 全部 +）：
- [ ] 架构合理？（职责清晰、依赖方向正确）
- [ ] 线程/并发安全？
- [ ] 事务边界正确？
- [ ] 向后兼容？（API、数据库、配置）
- [ ] 安全审查（调用 security-review 技能）
- [ ] 性能基准测试？
- [ ] 文档更新？
- [ ] 边界条件全覆盖？
```

## 审查流程

### 1. 理解变更

```bash
# 查看变更范围
git diff --stat main..HEAD
git log --oneline main..HEAD

# 阅读相关 PR 描述或计划文档
```

### 2. 选择深度

```
变更涉及支付/认证/数据库 schema？ → Deep
变更超过 300 行或跨 5+ 文件？    → Standard
其他                              → Quick
```

### 3. 逐文件审查

```markdown
审查顺序（从高风险到低风险）：
1. 数据库迁移/模型变更
2. API 路由/控制器
3. 业务逻辑 Service
4. UI 组件
5. 测试文件
6. 配置/工具文件
```

### 4. 输出审查报告

```markdown
## 代码审查报告

**范围：** [PR/分支/阶段]
**深度：** Standard
**审查者：** OPC Code Review Pipeline

### 摘要
[1-2 句话总结变更质量]

### 发现

#### 🔴 必须修复（阻塞合并）
1. `src/api/users.ts:45` — SQL 注入风险：用户输入直接拼接到查询

#### 🟡 建议修改
1. `src/services/user.ts:23` — `findAll` 缺少分页，大数据集会 OOM
2. `src/components/Form.tsx:67` — 表单提交无 loading 状态

#### 🔵 可选改进
1. `src/utils/format.ts:12` — 函数名 `fmt` 不够清晰，建议 `formatCurrency`

### 审查通过条件
- [x] Quick 清单
- [x] Standard 清单（除 🔴 发现）
- [ ] 🔴 发现修复后可合并
```

## 审查礼仪

- **指出问题，也认可优点**
- **提供具体修复建议**（不只说"这不对"）
- **区分"必须"和"建议"**
- **代码示例 > 文字描述**

## 一人公司审查策略

- 没有同事 → AI 是你的审查者
- 每个阶段/计划完成后自动触发 Standard 审查
- 支付/认证相关变更必须 Deep 审查
- 审查报告写入 SUMMARY.md 或 PR 描述

## 压力测试

### 高压场景
- PR 很大，想只做一次随意 review。

### 常见偏差
- 对所有变更都用同一深度审查。

### 使用技能后的纠正
- 按 quick/standard/deep 选择合适的审查深度。

