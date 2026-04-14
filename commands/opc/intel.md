---
name: opc-intel
description: Query, validate, diff, snapshot, or refresh codebase intelligence using the shipped IntelEngine runtime.
---

# /opc-intel

## Usage

```
/opc-intel <mode> [arguments]
```

## Modes

| 模式 | 用途 |
|------|------|
| `query <term>` | 搜索 `.opc/intel/*.json` 索引 |
| `status` | 查看索引文件新鲜度 |
| `validate` | 校验索引结构 |
| `snapshot` | 记录当前快照 |
| `diff` | 与上次快照对比变更 |
| `refresh` | 使用 `IntelEngine.refresh()` 重建索引并记录快照 |

## 流程

1. **走当前 CLI 合同**
   - `/opc-intel` 对应 `python bin/opc-tools intel ...`
   - `status/query/validate/snapshot/diff/refresh` 都是本地 runtime 行为
   - `refresh` 当前由 `scripts/engine/intel_engine.py` 内联执行，不再依赖额外代理接线才能工作

2. **查询与诊断**
   - `status` 检查 `stack.json`、`file-roles.json`、`api-map.json`、`dependency-graph.json`、`arch-decisions.json`
   - `query <term>` 在 key/value 中大小写不敏感搜索
   - `validate` 检查 `_meta` 与 `entries` 结构
   - `diff` 读取 `.opc/intel/.last-refresh.json`

3. **刷新索引**
   - `refresh` 会扫描当前项目、重写全部 5 个索引文件，并更新 `.last-refresh.json`
   - 输出包含写入路径和验证结果
   - 目标是提供一个稳定的最小闭环，而不是等待另一个编排层

## 索引文件

存储位置: `.opc/intel/`

| 文件 | 内容 |
|------|------|
| `stack.json` | 技术栈、框架、工具、构建系统摘要 |
| `file-roles.json` | 文件角色、导入/导出、入口类型 |
| `api-map.json` | 路由和 CLI 暴露面 |
| `dependency-graph.json` | package / requirements / pyproject 依赖摘要 |
| `arch-decisions.json` | 从当前代码结构归纳出的架构决策 |
| `.last-refresh.json` | 上次刷新快照哈希 |

## 推荐实现

```bash
python bin/opc-tools intel status --cwd /path/to/project
python bin/opc-tools intel query profile --cwd /path/to/project --raw
python bin/opc-tools intel validate --cwd /path/to/project --raw
python bin/opc-tools intel refresh --cwd /path/to/project --raw
python bin/opc-tools intel diff --cwd /path/to/project --raw
```

## 引擎

核心实现: `scripts/engine/intel_engine.py`

提供方法：
- `query(term)` — 关键词搜索
- `status()` — 新鲜度检查
- `validate()` — 结构验证
- `take_snapshot()` — 创建快照
- `diff()` — 与最近快照比对
- `refresh()` — 重建索引并快照

## 反模式

1. 不要手改 `.opc/intel/*.json` 作为常规流程
2. 不要把 `refresh` 继续描述成“仅代理派发”——现在已有本地 runtime
3. 不要把秘密、凭据或生成目录噪音写入索引
4. 不要把 `diff` 当作刷新——它依赖已有快照

## 参数

- `$ARGUMENTS` — 传递 `status`、`query <term>`、`validate`、`snapshot`、`diff` 或 `refresh`

## Related

- `/opc-research` — 产出可被上下文层复用的 intelligence 工件
- `/opc-dashboard` — 可引用 intel 数据
- `/opc-health` — 检查仓库/项目健康
