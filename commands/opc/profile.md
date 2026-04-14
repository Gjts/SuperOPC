---
name: opc-profile
description: Inspect the current developer profile, export it to markdown, or record interactions that update future profile inference.
---

# /opc-profile

## 流程

1. **走当前 CLI 合同，不做隐式刷新**
   - `/opc-profile` 对应 `python bin/opc-tools profile ...`
   - 当前可用子命令：`show`、`export`、`record`
   - 不再把 `--refresh` 作为单独模式文档化；画像更新通过 `record` 累积触发

2. **查看当前画像**
   - `show` 输出 8 维开发者画像
   - `show --injection` 输出给上下文组装器使用的精简注入片段

3. **导出或补充画像证据**
   - `export` 生成 `USER-PROFILE.md`
   - `record --command ... [--project ...] [--signals JSON]` 记录一次交互，用于后续推断更新

## 推荐实现

```bash
python bin/opc-tools profile show
python bin/opc-tools profile show --injection --raw
python bin/opc-tools profile export --dir /path/to/out
python bin/opc-tools profile record --command /opc-build --project superopc
python bin/opc-tools profile record --command /opc-plan --signals '{"communication":"terse"}'
```

## 输出约定

- `show`：返回 `developer_profile`，包括 communication / decision / debugging / UX / learning / explanation / stack / friction 等维度
- `show --injection`：返回供 `ContextAssembler` 直接消费的紧凑结构
- `export`：返回导出文件路径
- `record`：返回是否记录成功，以及对应命令/项目

## 存储

- 默认画像存储在 `~/.opc/USER-PROFILE.json`
- `export` 可另存为 markdown 快照
- `record` 是当前“refresh”的真实入口：它追加交互证据，而不是做一次性的强制重算

## 参数

- `$ARGUMENTS` — 传递 `show [--injection] [--raw]`、`export [--dir <path>]` 或 `record --command <cmd> [--project <name>] [--signals <json>]`

## Related

- `/opc-dashboard` — 展示受画像影响的建议
- `/opc-plan` — 计划阶段会消费画像注入
- `/opc-build` — 执行阶段可通过 `record` 积累行为证据
