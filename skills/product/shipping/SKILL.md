---
name: shipping
description: Use when development and review are complete. Guides branch completion with test verification, merge/PR options, and worktree cleanup.
---

## 发布流程

**宣布：** "我正在使用 shipping 技能来完成开发分支的交付。"

**核心原则：** 验证测试 → 呈现选项 → 执行选择 → 清理。

## 步骤 1: 验证测试

```bash
# 运行项目的测试套件
npm test / cargo test / pytest / go test ./... / dotnet test
```

- **如果测试失败** → 停止，显示失败信息，不继续
- **如果测试通过** → 继续步骤 2

## 步骤 2: 确定基础分支

```bash
git merge-base HEAD main
```

显示自基础分支以来的所有变更概要。

## 步骤 3: 呈现选项

```
开发完成。你想怎么处理？

1. 本地合并到 <base-branch>
2. 推送并创建 Pull Request
3. 保持当前分支（稍后处理）
4. 丢弃工作
```

## 步骤 4: 执行选择

### 选项 1: 本地合并
```bash
git checkout <base-branch>
git merge <feature-branch>
# 验证合并后测试
npm test
# 删除功能分支
git branch -d <feature-branch>
```

### 选项 2: 创建 PR
```bash
git push -u origin <feature-branch>
# 创建 PR（如果有 gh CLI）
gh pr create --title "<标题>" --body "<变更摘要和测试计划>"
```

### 选项 3: 保持原样
不做操作，提醒用户稍后处理。

### 选项 4: 丢弃
```bash
# 确认删除
git checkout <base-branch>
git branch -D <feature-branch>
```

## 步骤 5: 清理工作树

如果使用了 git worktree（选项 1 和 4 执行，选项 2 和 3 跳过）：
```bash
git worktree remove <worktree-path>
```

## 一人公司发布检查清单

发布前额外确认：
- [ ] 环境变量文档化了吗？
- [ ] 部署步骤记录了吗？
- [ ] 回滚方案准备好了吗？
- [ ] 监控/告警配置了吗？
- [ ] 用户文档更新了吗？

## 压力测试

### 高压场景
- 功能做完就想立刻发出去。

### 常见偏差
- 跳过验证、变更说明和回滚考虑。

### 使用技能后的纠正
- 先确认测试/验证/发布说明齐全，再执行 ship。

