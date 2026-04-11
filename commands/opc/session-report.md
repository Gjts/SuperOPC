---
name: opc-session-report
description: Summarize recent session activity, current progress, blockers, next steps, and validation debt for the active .opc project
---

# /opc-session-report — 会话报告

## 流程

1. **读取项目与会话材料**
   - `.opc/STATE.md`
   - `.opc/ROADMAP.md`
   - `.opc/REQUIREMENTS.md`
   - `.opc/HANDOFF.json`（如果存在）
   - 最近的 `.opc/sessions/*.json`

2. **汇总本轮会话**
   - 做了什么
   - 当前停在什么位置
   - 完成度变化
   - 新增 blockers / todos / risky decisions

3. **生成可复用报告**
   - 适合日结、handoff、复盘、经理视角
   - 保留一个主下一步
   - 明确 validation debt 和人工验证需求

4. **给出恢复入口**
   - 推荐 `/opc-resume` 或 `/opc-progress`
   - 如果需要正式交接，建议再执行 `/opc-pause`

## 建议输出结构

```markdown
## Session Summary
- 时间范围：...
- 工具/会话数：...
- 当前阶段 / 计划 / 状态：...

## What changed
- ...

## Current position
- 停止于：...
- 下一步：...

## Debt
- Blockers: ...
- Validation debt: ...
- Manual verification: ...
```

## 数据来源约定

- 当前状态以 `.opc/STATE.md` 为准
- 交接摘要优先读取 `.opc/HANDOFF.json`
- 会话时间线来自 `.opc/sessions/*.json`
- 如果没有会话文件，报告仍应根据 `.opc/` 主状态生成

## 推荐实现

```bash
python scripts/opc_session_report.py
python scripts/opc_session_report.py --cwd /path/to/project
python scripts/opc_session_report.py --cwd /path/to/project --json
```

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 或 `--json`
