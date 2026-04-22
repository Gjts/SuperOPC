---
name: opc-seed
description: Capture a forward-looking idea with surfacing triggers under .opc/seeds
---
# /opc-seed
想法种子入口。
## 动作
<!-- MIXED: list=readonly, create=writes .opc/seeds/ -->
调用 `python scripts/opc_seed.py $ARGUMENTS`。
保存现在不做、未来满足触发条件时应重新浮现的想法。
- **只读模式**：不带参数时列出现有种子
- **写入模式**：带新想法时会在 `.opc/seeds/` 创建单个 markdown 条目；stderr 会输出建议性 notice
  提示"需要验证该想法时可改用 `/opc-business`（validate-idea 子活动）"。设 `OPC_SUPPRESS_WRITE_ADVISORY=1` 静音
## 参数
- `$ARGUMENTS` — 想法、触发条件、备注或 `--cwd <path>`
