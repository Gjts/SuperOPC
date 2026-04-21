---
name: opc-intel
description: Query, validate, diff, snapshot, or refresh codebase intelligence with IntelEngine
---
# /opc-intel
代码库索引入口。支持 `status`、`query <term>`、`validate`、`snapshot`、`diff`、`refresh`。
## 动作
调用本地 runtime：`python bin/opc-tools intel $ARGUMENTS`。
`refresh` 由 `scripts/engine/intel_engine.py` 重建 `.opc/intel/` 五类索引并记录快照。
## 参数
- `$ARGUMENTS` — intel 子命令与参数
