# Git Workflow — SuperOPC Git 工作流规范

## 提交消息格式（Conventional Commits）

```
<type>(<scope>): <description>

<optional body>
```

### 类型

| type | 用途 |
|------|------|
| feat | 新功能 |
| fix | 修复 Bug |
| refactor | 重构（不改行为） |
| docs | 文档 |
| test | 测试 |
| chore | 构建/工具/依赖 |
| perf | 性能优化 |
| ci | CI/CD 配置 |

### scope 示例

```
feat(skills): add pricing skill
fix(agents): fix orchestrator delegation loop
docs(readme): update installation guide
test(hooks): add block-no-verify tests
```

## 分支策略（一人公司简化版）

```
main           ← 始终可部署
  └─ feat/*    ← 功能分支（短生命周期）
  └─ fix/*     ← 修复分支
```

- **main** 始终通过所有测试
- 功能分支从 main 创建，完成后合并回 main
- 不需要 develop / staging / release 分支（一人公司不需要复杂流程）

## Pull Request 流程

1. 分析完整提交历史（不仅是最后一个提交）
2. 使用 `git diff main...HEAD` 查看所有变更
3. 撰写全面的 PR 摘要
4. 包含测试计划

## Git 安全规则

- **永不** `git add .` 或 `git add -A` — 只暂存特定文件
- **永不** 在提交消息中包含密钥
- **永不** 使用 `--no-verify` 绕过 pre-commit hooks
- **始终** 推送前检查 `git diff --staged`
