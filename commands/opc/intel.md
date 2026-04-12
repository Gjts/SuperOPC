---
name: opc-intel
description: Query, inspect, or refresh codebase intelligence. Maintains a queryable JSON index of project structure, APIs, dependencies, and architecture.
---

# /opc-intel

## Usage

```
/opc-intel <mode> [arguments]
```

## Modes

| 模式 | 用途 |
|------|------|
| `query <term>` | 搜索代码库索引 |
| `status` | 查看索引文件新鲜度 |
| `diff` | 与上次快照对比变更 |
| `refresh` | 重建全部索引文件 |

## Behavior

### Step 0 — 横幅

执行前显示：
```
SuperOPC > INTEL
```

### Step 1 — 模式解析

解析 `$ARGUMENTS` 确定操作模式。无参数时显示用法说明。

### query \<term\>

在 `.opc/intel/` 下所有索引文件中搜索关键词（不区分大小写）。

搜索范围：JSON 文件的 key 和 value + arch-decisions.json 全文。

显示匹配条目，按来源文件分组。

**结束后 STOP。不派发代理。**

### status

检查每个索引文件的状态：
- 文件名
- 最后更新时间（`_meta.updated_at`）
- STALE（>24小时）或 FRESH 状态

**结束后 STOP。不派发代理。**

### diff

与上次快照对比（`.opc/intel/.last-refresh.json`）：
- 新增条目
- 删除条目
- 变更条目

如无快照，建议先运行 `refresh`。

**结束后 STOP。不派发代理。**

### refresh

派发 `opc-intel-updater` 代理分析代码库并写入/更新索引文件：

```
显示：SuperOPC > 正在派发 intel-updater 代理分析代码库...

Task(
  description="刷新代码库智能索引",
  prompt="你是 opc-intel-updater 代理。分析代码库并写入结构化索引到 .opc/intel/。
  
  项目根目录: ${CWD}
  
  参考代理定义: agents/opc-intel-updater.md
  
  完成后输出: ## INTEL UPDATE COMPLETE
  失败时输出: ## INTEL UPDATE FAILED"
)
```

代理完成后显示更新摘要。

## 索引文件

存储位置: `.opc/intel/`

| 文件 | 内容 |
|------|------|
| `stack.json` | 技术栈检测（语言/框架/工具/构建系统） |
| `file-roles.json` | 文件图谱（导出/导入/角色类型） |
| `api-map.json` | API 表面（路由/端点/命令） |
| `dependency-graph.json` | 依赖链（生产/开发/对等） |
| `arch-decisions.json` | 架构决策和模式 |

每个 JSON 文件包含 `_meta: { updated_at, version }` 元数据。

## 引擎

核心实现: `scripts/engine/intel_engine.py`

提供方法：
- `query(term)` — 关键词搜索
- `status()` — 新鲜度检查
- `diff()` — 快照对比
- `write_intel(key, data)` — 写入索引
- `take_snapshot()` — 创建快照
- `validate()` — 结构验证

## 反模式

1. 不要为 query/status/diff 操作派发代理 — 这些是内联操作
2. 不要直接修改索引文件 — 代理在 refresh 时处理写入
3. 不要在索引中包含密钥/凭据
4. 不要猜测 — 基于实际文件内容生成索引

## Related

- `/opc-research` — 市场研究工作流（市场情报方向）
- `/opc-dashboard` — 项目仪表盘（引用 intel 数据）
- `/opc-health` — 项目健康检查
