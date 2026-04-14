---
name: opc-research
description: Run the actual market-research pipeline: feed collection, insights extraction, methodology injection, report generation, and optional extracted-skill capture.
---

# /opc-research — 市场研究

## 流程

1. **走真实 runtime 管道**
   - `/opc-research` 对应 `python bin/opc-tools research ...`
   - 当前子命令：`feed`、`insights`、`methods list/show`、`run`
   - 主路径是 `run`：`feed -> insights -> methodology -> report -> extracted-skills`

2. **收集原始情报**
   - `feed --query <topic>` 调用 `compose_intelligence_report()`
   - 写入 `.opc/market_feed_latest.json` 等 feed 产物
   - 支持 `--days`、`--subreddit`、`--sources`

3. **提取结构化洞察**
   - `insights` 调用 `InsightGenerator`
   - 从最新 feed 或显式 `--feed <path>` 生成 `.opc/intelligence/insights-*.json`

4. **注入方法论并生成报告**
   - `run` 调用 `run_market_research()`
   - 自动从 `MethodologyDatabase` 注入方法论摘要
   - 输出 `.opc/research/YYYY-MM-DD-<topic>.md` + `.meta.json`
   - 默认镜像到 `docs/research/`，可用 `--no-mirror-docs` 关闭

5. **生成项目级 extracted skills**
   - `run` 默认还会调用 `SkillExtractor`
   - 产物写到当前项目的 `.opc/intelligence/extracted-skills/`
   - 这些文件会被 `ContextAssembler` 在 planning / discussing 时复用
   - 如需跳过，可传 `--no-extract-skills`

## 推荐实现

```bash
python bin/opc-tools research feed --query "developer tooling"
python bin/opc-tools research insights --cwd /path/to/project
python bin/opc-tools research methods list --domain validation --raw
python bin/opc-tools research run --query "AI developer tooling" --cwd /path/to/project --raw
python bin/opc-tools research run --query "founder CRM" --no-mirror-docs --no-extract-skills
```

## 输出约定

- `feed`：返回成功数据源、guardrail 状态、target niche
- `insights`：返回洞察条数和 top insight 摘要
- `methods list/show`：返回方法论索引或单个方法论详情
- `run`：返回 markdown/meta 路径、sources、methodologies，以及项目级 extracted-skills 输出位置与数量

## 工件

- `.opc/market_feed_latest.json`
- `.opc/intelligence/insights-*.json`
- `.opc/intelligence/methodologies/`（扩展方法论来源）
- `.opc/intelligence/extracted-skills/*.json`
- `.opc/research/YYYY-MM-DD-<slug>.md`
- `.opc/research/YYYY-MM-DD-<slug>.meta.json`
- 可选：`docs/research/YYYY-MM-DD-<slug>.md`

## 参数

- `$ARGUMENTS` — 传递 `feed --query <topic>`、`insights [--feed <path>]`、`methods list/show ...` 或 `run --query <topic> [--days N] [--subreddit name] [--sources a,b] [--no-mirror-docs] [--no-extract-skills]`
