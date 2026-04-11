---
name: opc-backlog
description: Park an idea in .opc/backlog so it remains visible and reviewable without entering the active roadmap yet
---

# /opc-backlog — 待规划池

## 用途

backlog 用于停放**值得保留，但暂时不进入主路线图**的事项。

适合：
- 已经有一定价值判断
- 比 seed 更具体
- 还不到进入 active roadmap / 正式 planning 的时机

## 模式

### 1. 无参数
列出 `.opc/backlog/` 下所有 backlog 条目：
- 编号 / 名称
- 状态
- 最近更新时间

### 2. 参数命中新描述
创建 backlog 条目：
- 写入 `.opc/backlog/BACKLOG-NNN-slug.md`
- 记录 Summary / Why Not Now / Dependencies / Promotion Trigger

### 3. 参数命中已有条目
读取 backlog 条目内容，帮助决定是否提升为线程、讨论、规划或 roadmap 项

## 存储约定

- 路径：`.opc/backlog/BACKLOG-NNN-slug.md`
- backlog 是停放池，不是正式 phase 编号系统
- 与 seed 的区别：backlog 已经更接近“待规划事项”，而非远期信号

## 推荐实现

```bash
python scripts/opc_backlog.py
python scripts/opc_backlog.py <description>
python scripts/opc_backlog.py <description> --note "为什么先不做"
python scripts/opc_backlog.py --cwd /path/to/project
```

## 关系

- 只是未来线索，还不想承诺 → `/opc-seed`
- 需要跨会话持续跟进 → `/opc-thread`
- 已经准备讨论或转规划 → `/opc-discuss` / `/opc-plan`

## 参数

- `$ARGUMENTS` — backlog 描述
- 可选 `--note <text>` — 为什么先停放、不现在推进
