---
name: opc-health
description: Run SuperOPC quality-system checks for a project or this repository, report integrity and quality debt, and optionally apply safe repairs
---

# /opc-health — 质量健康检查

## 流程

1. **识别检查目标**
   - 如果当前目录存在 `.opc/`，按项目模式检查
   - 否则按仓库模式检查 source-of-truth 仓库结构

2. **执行完整性检查**
   - 项目模式：`.opc/` 核心文件、支撑目录、`config.json`、`HANDOFF.json`
   - 仓库模式：`agents/`、`commands/opc/`、`hooks/hooks.json`、`.claude-plugin/plugin.json`、`skills/`、`templates/`

3. **执行 v0.9.0 质量检查**
   - requirements → roadmap 覆盖
   - SUMMARY frontmatter 中的 `requirements-completed`
   - 恢复文件引用是否存在
   - source markdown frontmatter 是否完整
   - plugin / hook 引用是否接线正确
   - 内部 markdown 链接是否有效

4. **可选修复**
   - 仅修复安全、确定性的缺失结构
   - 如补齐 `.opc/` 目录、核心模板文件、支撑目录、`config.json`、`HANDOFF.json`
   - 不自动改写需求、路线图或业务内容

## 推荐脚本

```bash
python scripts/opc_health.py
python scripts/opc_health.py --cwd /path/to/project
python scripts/opc_health.py --cwd /path/to/project --repair
python scripts/opc_health.py --cwd /path/to/project --json
python scripts/opc_health.py --cwd /path/to/repo --target repo --json
```

## 输出约定

- 默认输出人类可读摘要
- `--json` 输出结构化结果：target / summary / checks / repairs
- 返回非 0 退出码表示仍有未解决失败项

## 参数

- `$ARGUMENTS` — 可选，传递 `--cwd <path>`、`--repair`、`--json`、`--target project|repo|all`
