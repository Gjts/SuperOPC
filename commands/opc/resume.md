---
name: opc-resume
description: Reconstruct working context from HANDOFF, STATE, roadmap, and recent session artifacts
---
# /opc-resume
恢复会话入口。
## 动作
调用 `python scripts/opc_resume.py $ARGUMENTS`。
重建上下文，校验恢复文件，刷新连续性字段，并推荐第一个动作。
## 参数
- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 或恢复目标
