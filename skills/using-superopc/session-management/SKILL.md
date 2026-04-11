---
name: session-management
description: Use when the task is about pausing, resuming, checkpointing, reporting, or recovering SuperOPC project context across sessions.
---

# 会话管理

当用户想暂停、恢复、查看当前位置、生成会话报告，或在跨会话之间保持连续性时使用本技能。

## 目标

把当前工作压缩成对下一次会话真正有用的信息，而不是复制整段上下文。

## 核心规则

1. **优先读 `.opc/HANDOFF.json`**，没有再回退到 `.opc/STATE.md`
2. **`STATE.md` 是项目真相源**，handoff 是会话级检查点
3. **输出一个主下一步**，不要给很多并行建议
4. **明确 validation debt**，不要把未验证内容伪装成完成

## 子场景

### Pause
- 记录当前停止点
- 记录一个主下一步
- 记录 blockers / todos / 恢复文件
- 更新 `STATE.md` 的会话连续性字段

### Resume
- 重建当前位置
- 检查 handoff 是否仍有效
- 如果 handoff 与当前状态冲突，以最新事实为准

### Progress
- 输出位置、完成度、下一步、验证欠债

### Session report
- 汇总最近会话、当前状态、handoff、audit log

## 反模式

- 把 handoff 写成长篇流水账
- 不区分项目状态和会话状态
- 给出多个平行“下一步”导致分心
- 忽略恢复文件是否仍存在
