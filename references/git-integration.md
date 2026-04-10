# Git Integration — Git 集成参考

SuperOPC 中 Git 操作的标准模式和最佳实践。

---

## 提交策略

### 原子提交
- 每个提交完成一件事
- 可独立回滚
- `git bisect` 在提交级别工作

### 提交频率
- 功能完成一个逻辑单元 → 提交
- TDD 每个阶段一个提交（RED/GREEN/REFACTOR）
- 不要积累大量未提交的变更

### 提交消息

```
<type>(<scope>): <description>

<optional body explaining WHY, not WHAT>

<optional footer: Breaking Changes, Closes #issue>
```

## 分支策略

### 一人公司简化流程

```
main ─── 始终可部署
  │
  ├── feat/user-auth ─── 短生命周期功能分支
  │     └── 完成后合并并删除
  │
  └── fix/login-bug ─── 修复分支
        └── 完成后合并并删除
```

### 分支命名
- `feat/short-description`
- `fix/short-description`
- `docs/short-description`

## Git Worktree（隔离工作空间）

当需要同时处理多个任务时，使用 Git Worktree 而非分支切换：

```bash
# 创建工作树
git worktree add ../project-feat-auth feat/user-auth

# 列出工作树
git worktree list

# 清理
git worktree remove ../project-feat-auth
```

**优势：**
- 不需要 stash 当前工作
- 每个任务有独立的工作目录
- 适合一人公司频繁切换任务的场景

## 安全规则

- **永不** `git add .` — 暂存特定文件
- **永不** `--no-verify` — hooks 存在有其原因
- **永不** 在提交中包含密钥
- **始终** 推送前 `git diff --staged`

## 紧急恢复

```bash
# 撤销最后一次提交（保留变更）
git reset --soft HEAD~1

# 撤销暂存
git reset HEAD <file>

# 恢复文件到上次提交
git checkout -- <file>

# 从意外 reset 恢复
git reflog
git reset --hard <commit-hash>
```
