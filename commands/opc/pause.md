---
name: opc-pause
description: Capture a resumable checkpoint by updating continuity fields and writing .opc/HANDOFF.json
---
# /opc-pause
暂停与交接入口。
## 动作
调用 `python scripts/opc_pause.py $ARGUMENTS`。
写入 `.opc/HANDOFF.json`，更新 `STATE.md` 连续性字段，并输出恢复提示。
## 参数
- `$ARGUMENTS` — 可选，暂停原因、stop point、`--cwd <path>`
