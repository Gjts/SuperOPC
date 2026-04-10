---
name: opc-dashboard
description: Show a live operating dashboard for the current .opc project, including progress, business metrics, debt, and next step
---

# /opc-dashboard — 项目仪表盘

## 流程

1. **读取项目状态**
   - `.opc/PROJECT.md`
   - `.opc/REQUIREMENTS.md`
   - `.opc/ROADMAP.md`
   - `.opc/STATE.md`

2. **输出经营全貌**
   - 当前阶段 / 当前计划 / 当前状态
   - 阶段、计划、需求完成度
   - MRR / Burn / Runway / 活跃客户（若已记录）
   - 阻塞、待办、待复核决策

3. **给出下一步**
   - 显示路线图中下一个未完成计划
   - 如果 `STATE.md` 有更新，优先展示最近活动

## 推荐脚本

```bash
python scripts/opc_dashboard.py
python scripts/opc_dashboard.py --cwd /path/to/project
```

## 数据来源约定

- 商业指标优先从 `.opc/STATE.md` 的“商业指标”部分读取
- 如果没有记录 MRR/Burn/Runway，命令会保留 `未记录` 并提示补充
- `todos/` 目录中的文件会被计入项目债务

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>` 指向目标项目
