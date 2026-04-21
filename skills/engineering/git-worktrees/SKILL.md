---
name: git-worktrees
description: Use when starting new feature development that needs an isolated workspace. Creates safe git worktrees with automatic project setup and test verification.
id: git-worktrees
type: atomic
tags: [git, worktree, isolated, workspace, branch]
triggers:
  keywords: [worktree, 工作树, 隔离分支, 新分支, feature branch]
version: 1.4.1
---

## Git Worktree 管理

**宣布：** "我正在使用 git-worktrees 技能来创建隔离的开发环境。"

## 何时使用

- 新功能开发（需要与主分支隔离）
- 实验性改动（可能需要丢弃）
- 并行开发多个功能

## 步骤 1: 确定目录

```bash
# 按优先级检查
ls -d .worktrees 2>/dev/null     # 首选（隐藏）
ls -d worktrees 2>/dev/null      # 备选
```

如果都不存在，创建 `.worktrees/`。

## 步骤 2: 安全验证

```bash
# 确认目录被 gitignore
git check-ignore -q .worktrees 2>/dev/null
```

**如果没有被忽略 → 立即修复：**
1. 添加到 `.gitignore`
2. 提交变更
3. 然后继续

## 步骤 3: 创建 Worktree

```bash
# 确定路径
BRANCH_NAME="feature/<feature-name>"
WORKTREE_PATH=".worktrees/<feature-name>"

# 创建 worktree 和新分支
git worktree add "$WORKTREE_PATH" -b "$BRANCH_NAME"
cd "$WORKTREE_PATH"
```

## 步骤 4: 项目设置

自动检测项目类型并安装依赖：

```bash
# Node.js
if [ -f package.json ]; then npm install; fi

# Rust
if [ -f Cargo.toml ]; then cargo build; fi

# Python
if [ -f requirements.txt ]; then pip install -r requirements.txt; fi

# .NET
if [ -f *.sln ]; then dotnet restore; fi
```

## 步骤 5: 验证基线

```bash
# 运行测试确认环境正常
npm test / cargo test / pytest / dotnet test
```

**所有测试必须通过。** 如果有失败，在开始工作前先解决。

## 清理

开发完成后（通过 shipping 技能处理）：
```bash
git worktree remove <worktree-path>
```

## 集成点

- **brainstorming 技能** → 设计批准后建议创建 worktree
- **implementing 技能** → 在 worktree 中执行计划
- **shipping 技能** → 完成后清理 worktree

## 压力测试

### 高压场景
- 想并行做多个分支任务，但都在同一个工作区操作。

### 常见偏差
- 在一个目录里反复切分支，污染未提交状态。

### 使用技能后的纠正
- 为并行任务建立独立 worktree，隔离上下文和改动。

