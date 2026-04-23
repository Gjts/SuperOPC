---
name: opc-profile
description: Inspect, export, or record developer-profile signals
---
# /opc-profile
开发者画像入口。
## 动作
调用 `python bin/opc-tools profile $ARGUMENTS`。
`show` / `export` 读取现有画像；`record` 会写本地 profile，不写项目 `.opc/`。
## 参数
- `$ARGUMENTS` — profile 子命令与参数
