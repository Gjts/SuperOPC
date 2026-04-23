# SuperOPC 目录地图

这份文档说明仓库里每个顶层目录的职责，并区分哪些是正式源码，哪些是生成物或本地运行产物。

## 一、正式源码与文档

| 目录 | 角色 | 说明 |
| --- | --- | --- |
| `agents/` | Agent workflow | 27 个 agent 的完整工作流定义与 `registry.json`。 |
| `commands/` | Slash 入口 | `commands/opc/*.md`，15 行以内的命令入口文档。 |
| `skills/` | Skill 层 | dispatcher / atomic / learning skills 与 `registry.json`、schema。 |
| `references/` | 知识库 | business、engineering patterns、review rubric 等只读方法论。 |
| `scripts/` | 运行时实现 | CLI、engine、hooks、intel、quality、convert 等 Python 实现。 |
| `tests/` | 自动化验证 | repo contract、engine、CLI、session、quality、user scenarios 测试。 |
| `templates/` | 脚手架模板 | `.opc` 文件模板与 starter project 模板。 |
| `docs/` | 设计与说明 | ADR、目录地图、用户场景矩阵与 `docs/archive/` 中的历史设计档案。 |
| `docs/archive/` | 历史设计档案 | 已完成或已废弃的设计提案、重构蓝图与融合档案；保留作历史参考，不是当前 source of truth。 |
| `examples/` | 示例流程 | SaaS MVP、API、business workflow 示例。 |
| `rules/` | 代码规则 | common / python / typescript / csharp / kotlin 规则集。 |
| `hooks/` | Hook 注册 | 顶层 hook 配置入口。 |
| `mcp-configs/` | MCP 模板 | 可复制的 MCP server 配置。 |
| `bin/` | CLI 薄入口 | `opc-tools` 的可执行 wrapper。 |
| `.claude-plugin/` | 插件清单 | Claude 插件 manifest，需和 agents/commands/skills 对齐。 |
| `marketing/` | 发布素材 | 当前发布素材与 `marketing/archive/` 中的版本化历史文案。 |
| `marketing/archive/` | 历史发布资产 | 旧版本 launch copy；保留用于复盘，不应直接复用到当前版本。 |
| `website/` | 官网落地页 | 静态网站与部署说明，由 GitHub Pages workflow 消费。 |

## 二、生成物

| 目录 | 角色 | 说明 |
| --- | --- | --- |
| `integrations/` | 多运行时导出 | `python scripts/convert.py --tool ...` 生成的运行时产物。不是 source of truth；目录内的 [README](../integrations/README.md) 约束其只读/再生使用方式。 |

## 三、本地运行与临时目录

这些目录不应作为正式源码维护，通常也不应提交到仓库。

| 目录 | 角色 | 说明 |
| --- | --- | --- |
| `.opc/` | 本地项目状态 | 会话、handoff、routing、research、threads、todos 等运行时状态。 |
| `.claude/` | 本地工作目录 | Claude/Codex 类工具的本地工作树与辅助状态。 |
| `.manual_verify/` | 手工验证产物 | smoke / debug / case 级别的临时验证目录。 |
| `.pytest_tmp/` | 历史 pytest 临时目录 | 旧的本地测试产物。 |
| `.test_tmp/` | 仓库内临时测试根 | 受控测试/调试目录，默认应忽略。 |
| `pytest-cache-files-*` | pytest 异常缓存目录 | Windows 下偶发的临时缓存残留，应视为噪音。 |

## 四、目录使用约定

- 优先把真实实现放进 `scripts/`，不要把逻辑写进 `commands/`、`agents/` 或生成目录。
- `agents/` 持有完整 workflow；`commands/` 只做入口；`skills/` 只做 dispatch 或 atomic 能力。
- `references/` 只放知识，不放可执行流程。
- `integrations/` 只在需要验证导出结果时查看，不手工作为主编辑面；若运行时导出过期，直接重跑 `python scripts/convert.py --tool all`。
- 新增一个顶层目录前，先判断它属于“正式源码”、“生成物”还是“本地状态”，并同步更新本文件。

## 五、排查顺序

如果你第一次进入仓库，建议按下面的顺序理解：

1. 看 `README.md` 和 `AGENTS.md`，先理解命令契约和 agent 架构。
2. 看 `docs/COMMAND-CHEAT-SHEET.md`，理解用户入口。
3. 看本文件，知道每个目录的职责和边界。
4. 真正改实现时，优先进入 `scripts/`、`agents/`、`skills/`、`tests/`。
