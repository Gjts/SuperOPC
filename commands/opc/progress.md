---
name: opc-progress
description: Show the current working position, next step, completion status, blockers, and verification debt for the active .opc project
---

# /opc-progress — 进度与位置

## 流程

1. **读取当前项目状态**
   - `.opc/STATE.md`
   - `.opc/ROADMAP.md`
   - `.opc/REQUIREMENTS.md`
   - 最新的 `.opc/sessions/*.json`（如果存在）

2. **展示当前位置**
   - 当前阶段 / 当前计划 / 当前状态
   - 最近活动 / 停止于 / 恢复文件
   - 阶段、计划、需求完成度
   - requirements / regression / scope / traceability / schema 质量债务摘要

3. **给出一个主下一步**
   - 优先显示路线图中下一个未完成计划
   - 如果 `STATE.md` 已记录阻塞，先提示解除阻塞
   - 根据当前状态推荐 `/opc-plan`、`/opc-build`、`/opc-review`、`/opc-discuss` 或 `/opc-next`

4. **显示执行风险**
   - blockers / todos / risky decisions
   - validation debt（待验证项、未运行检查、人工验证欠债）
   - quality debt（requirements coverage、跨阶段回归、scope reduction、claim traceability、schema drift）
   - 最近一次会话记录和 handoff（如存在）

## 输出约定

- **位置**：阶段 / 计划 / 状态 / 停止点
- **完成度**：phase / plan / requirement 百分比或计数
- **下一步**：只给一个主建议，避免分散注意力
- **验证欠债**：明确区分“已验证”与“尚未验证”

## 推荐实现

```bash
python scripts/opc_progress.py
python scripts/opc_progress.py --cwd /path/to/project
python scripts/opc_progress.py --cwd /path/to/project --json
```

## 读取优先级

1. `.opc/STATE.md` 中的当前位置与阻塞
2. `.opc/ROADMAP.md` 中的下一个未完成计划
3. `.opc/REQUIREMENTS.md` 中的完成度
4. `.opc/sessions/` 中最近会话的时间戳和工具来源

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 或 `--json`
