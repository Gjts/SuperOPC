---
name: opc-next
description: Recommend the next best command or action based on current .opc state, roadmap progress, and blockers
---

# /opc-next — 下一步建议

## 流程

1. **读取当前项目状态**
   - `.opc/STATE.md`
   - `.opc/ROADMAP.md`
   - `.opc/REQUIREMENTS.md`

2. **判断下一步**
   - 如果有 blockers，优先建议 `/opc-discuss`
   - 如果处于规划状态，建议 `/opc-plan`
   - 如果处于执行状态，建议 `/opc-build`
   - 如果阶段完成，建议 `/opc-review` 或 `/opc-ship`
   - 如果信号不足，退回讨论模式

3. **输出推荐理由**
   - 不是只给命令名，也说明为什么现在该做它

## 推荐脚本

```bash
python scripts/opc_next.py
python scripts/opc_next.py --cwd /path/to/project
python scripts/opc_next.py --cwd /path/to/project --json
```

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 或 `--json`
