---
name: opc-resume
description: Reconstruct working context from .opc/HANDOFF.json, STATE.md, and recent session artifacts, then recommend the first action to take
---

# /opc-resume — 恢复会话

## 流程

1. **读取恢复材料**
   - `.opc/HANDOFF.json`
   - `.opc/STATE.md`
   - `.opc/ROADMAP.md`
   - 最新的 `.opc/sessions/*.json`（如果存在）

2. **重建上下文**
   - 当前阶段 / 计划 / 状态
   - 上次停止点
   - 主下一步 / 备选下一步
   - blockers / validation debt / resume files

3. **校验可恢复性**
   - 恢复文件是否存在
   - 路线图位置是否仍然有效
   - 如果 handoff 与当前状态冲突，以最新事实为准，并提示用户

4. **输出恢复建议**
   - 一个主动作：先读哪个文件、先做哪件事
   - 如果有未验证改动，先建议验证
   - 如果 handoff 过期或缺失，回退到 `/opc-progress`

## 恢复优先级

1. `.opc/HANDOFF.json` — 最近一次人工整理的交接摘要
2. `.opc/STATE.md` — 项目活状态
3. `.opc/ROADMAP.md` — 当前阶段与下一个计划
4. `.opc/sessions/*.json` — 会话时间线补充信息

## 冲突处理

- **handoff 有、state 更新了**：以 `STATE.md` 为当前位置，以 handoff 作为补充说明
- **handoff 缺失**：退回读取 `STATE.md` + `/opc-progress`
- **恢复文件不存在**：提示路径失效，不要静默继续
- **blockers 未清理**：先建议处理 blocker，再继续执行

## 推荐实现

```bash
python scripts/opc_resume.py
python scripts/opc_resume.py --cwd /path/to/project
```

如果尚未提供专用脚本，可按以上优先级手动恢复，并把结果写回 `STATE.md`。当前 `python scripts/opc_resume.py` 会在恢复时同步刷新 `STATE.md` 的会话连续性字段。

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 或附加恢复目标
