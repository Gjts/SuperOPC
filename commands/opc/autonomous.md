---
name: opc-autonomous
description: Advance a bounded slice of roadmap work autonomously, while stopping at blockers, verification debt, or human checkpoints
---

# /opc-autonomous — 有边界自主推进

## 定位

`/opc-autonomous` 适合在**范围已知、状态清楚、边界明确**时，减少逐步确认，连续推进一段工作。

它不是“无限自动执行”。
它必须在以下情况停下：
- 出现 blocker
- 发现新的范围分歧
- 遇到人工决策或人工验证检查点
- 验证欠债已经影响继续推进

## 流程

1. **读取当前工作状态**
   - `.opc/STATE.md`
   - `.opc/ROADMAP.md`
   - `.opc/REQUIREMENTS.md`
   - `.opc/HANDOFF.json`（如果存在）
   - 当前恢复文件 / 当前计划窗口

2. **确定自主推进边界**
   - 默认从当前计划开始
   - `--from N --to N` 指定连续窗口
   - `--only N` 只推进一个计划编号
   - `--interactive` 保留人工检查点，在 checkpoint 处停下

3. **执行前先做闸门判断**
   - 如果存在 blocker，先退回 `/opc-discuss`
   - 如果 validation debt 或 quality debt 已影响继续执行，先退回 `/opc-progress` 或 `/opc-health`
   - 如果计划包含 `checkpoint:decision` 或 `checkpoint:human-verify`，切换为交互式推进

4. **输出自主执行序列**
   - 当前状态与目标窗口
   - 建议命令与理由
   - 恢复入口
   - 下一组可连续推进的动作

## 边界规则

- `/opc-fast`：一个微任务
- `/opc-quick`：1-3 个任务的小流程
- `/opc-autonomous`：在既定边界内连续推进一段工作
- `/opc-build`：执行正式计划与完整实现路径

## 推荐脚本

```bash
python scripts/opc_autonomous.py
python scripts/opc_autonomous.py --cwd /path/to/project
python scripts/opc_autonomous.py --cwd /path/to/project --from 2 --to 4
python scripts/opc_autonomous.py --cwd /path/to/project --only 3 --interactive
python scripts/opc_autonomous.py --cwd /path/to/project --json
```

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>`、`--from N`、`--to N`、`--only N`、`--interactive`、`--json`
