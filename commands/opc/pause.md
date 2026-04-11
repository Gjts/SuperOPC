---
name: opc-pause
description: Capture a resumable checkpoint for the current .opc project by updating continuity fields and writing .opc/HANDOFF.json
---

# /opc-pause — 暂停并交接

## 流程

1. **读取当前上下文**
   - `.opc/STATE.md`
   - `.opc/ROADMAP.md`
   - `.opc/REQUIREMENTS.md`
   - 当前工作中最关键的文件 / 计划 / 阻塞

2. **更新会话连续性**
   - 刷新 `STATE.md` 中的：
     - 上次会话
     - 停止于
     - 恢复文件
     - 最近活动
   - 如有新阻塞或新待办，写回对应区块

3. **写入 `.opc/HANDOFF.json`**
   - 记录时间戳、当前位置、完成度、下一步、推荐命令
   - 记录 blockers / todos / resume hints
   - 可选附加一条简短备注和 stop point

4. **输出恢复提示**
   - 提醒下次先运行 `/opc-resume` 或 `/opc-progress`
   - 明确建议恢复命令与理由

## HANDOFF 约定

- 交接文件路径：`.opc/HANDOFF.json`
- 目标：**读一次就知道从哪里恢复**
- 只保留对下一次会话有用的信息，不做长篇归档
- 结构参考：`templates/handoff.json`

## 何时使用

- 结束当前会话前
- 切换到另一项工作前
- 上下文即将过载，需要主动检查点时
- 需要把工作交给未来的自己或其他代理时

## 写入守则

- 使用当前事实，不写猜测
- 不复制整个终端日志
- 不罗列很多下一步，优先一个主动作
- 如果存在未验证实现，必须明确标注为 validation debt

## 参数

- `$ARGUMENTS` — 可选，补充一句暂停原因或恢复提示
