---
name: opc-seed
description: Capture a forward-looking idea with surfacing triggers under .opc/seeds so it can be revisited at the right time
---

# /opc-seed — 想法种子

## 用途

种子用于保存**现在不做、但未来可能应该主动浮现**的想法。

适合：
- 当前范围外，但有明确潜力
- 依赖某个触发条件才值得推进
- 现在不进入 roadmap，也不想在 backlog 中过早承诺

## 模式

### 1. 无参数
列出 `.opc/seeds/` 下所有种子：
- 编号 / 名称
- 状态
- 触发条件
- 最近更新时间

### 2. 参数命中新种子描述
创建种子：
- 写入 `.opc/seeds/SEED-NNN-slug.md`
- 记录 Why Later / Trigger / References / First Move When Surfaced

### 3. 参数命中现有种子
读取现有种子内容，帮助判断是否该浮现到线程、backlog 或正式计划

## 存储约定

- 路径：`.opc/seeds/SEED-NNN-slug.md`
- 默认状态：`DORMANT`
- 必须记录触发条件，避免想法变成无人再看的单行备忘

## 推荐实现

```bash
python scripts/opc_seed.py
python scripts/opc_seed.py <idea>
python scripts/opc_seed.py <idea> --trigger "当满足某条件时"
python scripts/opc_seed.py --cwd /path/to/project
```

## 关系

- 已经需要持续维护上下文 → `/opc-thread`
- 已经确定要进入待规划池 → `/opc-backlog`
- 只是先记录未来方向与浮现条件 → `/opc-seed`

## 参数

- `$ARGUMENTS` — 种子想法描述
- 可选 `--trigger <text>` — 指定浮现触发条件
