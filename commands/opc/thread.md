---
name: opc-thread
description: Create, list, or resume lightweight persistent context threads stored under .opc/threads for cross-session work
---

# /opc-thread — 上下文线程

## 用途

线程用于保存**跨会话但不属于某个阶段计划**的持续上下文。

适合：
- 长时间调查中的问题
- 暂时不进入 roadmap 的研究线索
- 需要多次回来继续的思路
- 以后还会继续推进，但现在不想写成 HANDOFF 的事项

## 模式

### 1. 无参数
列出 `.opc/threads/` 下所有线程：
- 名称
- 状态
- 最近更新时间

### 2. 参数命中现有线程
恢复并展示该线程内容：
- 读取线程文件
- 如果状态为 `OPEN`，可标记为 `IN_PROGRESS`
- 让当前会话快速进入该上下文

### 3. 参数是新描述
创建新线程：
- 生成 slug 文件名
- 写入 `.opc/threads/<slug>.md`
- 记录目标、上下文、引用、下一步

## 存储约定

- 路径：`.opc/threads/*.md`
- 线程是**非阶段绑定**的上下文存储
- 比 `/opc-pause` 更轻，不承担项目状态同步职责
- 线程成熟后，可转成 backlog 或进入正式计划

## 推荐实现

```bash
python scripts/opc_thread.py
python scripts/opc_thread.py <description>
python scripts/opc_thread.py <thread-name>
python scripts/opc_thread.py --cwd /path/to/project
```

## 关系

- 想保存“以后某个时机再看”的想法 → `/opc-seed`
- 想停放到待规划池中 → `/opc-backlog`
- 想保存当前主工作检查点 → `/opc-pause`

## 参数

- `$ARGUMENTS` — 可选；为空则列出线程，有值则创建或恢复线程
