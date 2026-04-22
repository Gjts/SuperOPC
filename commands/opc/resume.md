---
name: opc-resume
description: Resume session — dispatches session-management skill which owns the workflow
---
# /opc-resume — 恢复会话入口
用户显式触发会话恢复。等价于自然语言 "继续上次" / "从哪里开始"。
## 动作
调用 `session-management` skill，传入 `$ARGUMENTS`，并在意图上下文附加 `sub_scenario=resume`。
session-management skill 会派发 `opc-session-manager` agent 执行 Resume 子场景（读 `HANDOFF.json` → 校验 recovery files → 对齐 `STATE.md` → 重建当前位置 + 推荐一个主下一步）。
## 跨机器 / 跨会话协议
- `.opc/HANDOFF.json` 与 `.opc/STATE.md` **应该** commit 到 git（它们是跨会话协作的契约）
- `.opc/sessions/*.md` 和 `.opc/cruise-log/*.jsonl` **不应该** commit（会话级临时文件，gitignore）
- **跨机恢复** workflow：
  1. 机器 A：`/opc-pause --note "..."` → commit HANDOFF.json + STATE.md → push
  2. 机器 B：pull → `/opc-resume` → opc-session-manager 读 handoff
  3. recovery_files 若含绝对路径（如 `C:/Users/...`），opc-session-manager 会尝试映射到 `${REPO_ROOT}` 相对路径；无法映射时会列出需手动修复的项
- **多人协作**：HANDOFF.json 同一时刻只能有一个 owner；若 pull 后发现 handoff 已被他人修改，opc-session-manager 会显示冲突并询问是否接管
## 常见错误与修复
- **`HANDOFF.json` 不存在** → opc-session-manager 回退到读 `STATE.md` 重建上下文；若 STATE.md 也缺失会建议 `/opc-start` 重新初始化
- **recovery_files 指向的文件已被删除/重命名** → 列出冲突项并询问用户确认跳过或手动修复
- **handoff 已过期**（阶段早已完成） → 询问是否归档到 `.opc/archive/handoffs/<date>-<slug>.json`
## 参数
- `$ARGUMENTS` — 可选，`--cwd <path>` 或恢复目标
