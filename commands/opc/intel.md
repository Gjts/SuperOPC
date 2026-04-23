---
name: opc-intel
description: Query, validate, diff, snapshot, or refresh codebase intelligence with IntelEngine
---
# /opc-intel
代码库索引入口。支持 `status`、`query <term>`、`validate`、`snapshot`、`diff`、`refresh`。
## 动作
查询类子命令调用本地 runtime：`python bin/opc-tools intel $ARGUMENTS`。
`refresh` 不走本地 runtime；调用 `workflow-modes` skill，并附加 `sub_scenario=intel-refresh`，由 `opc-intel-updater` 执行。
## 参数
- `$ARGUMENTS` — intel 子命令与参数
