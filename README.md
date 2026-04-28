# SuperOPC

SuperOPC 是一个给 Codex / Claude Code 等 AI 编码工具使用的本地工作流插件源仓库。

它的核心不是一个 Web 服务，而是一套可以被导出的 agent、skill、slash command、hook 和 Python runtime。目标是让一个人也能按“规划 -> 构建 -> 审查 -> 发布 -> 调试 -> 运营”的流程推进项目。

## 当前可真实使用的方式

### 1. 克隆仓库

```bash
git clone https://github.com/gjts/superopc.git
cd superopc
```

### 2. 生成目标运行时包

```bash
python scripts/convert.py --tool codex
python scripts/convert.py --tool claude-code
python scripts/convert.py --tool all
```

生成结果默认写入 `integrations/<tool>/`。`integrations/` 是可再生输出目录，仓库不跟踪其中内容；需要时由转换器自动创建。

### 3. Codex 中真实执行 agent workflow

默认 Codex 模式只解析 dispatcher -> agent，并写入 handoff：

```powershell
$env:SUPEROPC_AGENT_RUNTIME = "codex"
python bin\opc-tools --raw dispatch --skill planning -- "plan login flow"
```

需要真实启动 `codex exec` 跑 agent workflow 时：

```powershell
$env:SUPEROPC_AGENT_RUNTIME = "codex-exec"
python bin\opc-tools --raw dispatch --skill planning -- "plan login flow"
```

### 4. 健康检查和测试

```bash
python scripts/opc_health.py --cwd . --target repo --json
python scripts/verify_command_contract.py
python scripts/build_skill_registry.py --check
python scripts/run_pytest.py tests/ -v
```

## 核心命令

| 命令 | 作用 | 路径 |
| --- | --- | --- |
| `/opc-start` | 初始化 `.opc/` 项目状态 | dispatcher |
| `/opc-plan` | 规划功能，派发 `opc-planner` | dispatcher |
| `/opc-build` | 执行开发，派发 `opc-executor` | dispatcher |
| `/opc-review` | 代码审查，派发 `opc-reviewer` | dispatcher |
| `/opc-ship` | 发布/合并/PR，派发 `opc-shipper` | dispatcher |
| `/opc-debug` | 系统化调试，派发 `opc-debugger` | dispatcher |
| `/opc-security` | 安全审计，派发 `opc-security-auditor` | dispatcher |
| `/opc-business` | 商业/定价/验证/MVP 建议 | dispatcher |
| `/opc-progress` | 查看当前进度 | session dispatcher |
| `/opc-pause` / `/opc-resume` | 跨会话交接和恢复 | session dispatcher |
| `/opc-cruise` / `/opc-autonomous` | 有边界自主推进 | autonomous dispatcher |
| `/opc-health` | 本地健康检查和安全修复 | local runtime |
| `/opc-dashboard` / `/opc-stats` | 只读项目面板和统计 | local runtime |
| `/opc-thread` / `/opc-seed` / `/opc-backlog` | 轻量上下文、想法、待办捕获 | mixed local runtime |

## 核心目录

| 目录 | 是否核心 | 用途 |
| --- | --- | --- |
| `agents/` | 是 | 27 个 agent workflow 和 `registry.json` |
| `skills/` | 是 | dispatcher / atomic / meta skills |
| `commands/opc/` | 是 | slash command 入口 |
| `scripts/` | 是 | CLI、dispatch、engine、quality、convert 的真实实现 |
| `templates/` | 是 | `.opc` 初始化、config、handoff、phase artifact 模板 |
| `references/` | 是 | agent workflow 引用的工程/商业/审查知识库 |
| `rules/` | 是 | 多语言编码、测试、安全规则 |
| `hooks/` | 是 | hook 注册表 |
| `bin/` | 是 | `opc-tools` CLI wrapper |
| `.codex-plugin/` | 是 | Codex 本地插件 manifest |
| `.claude-plugin/` | 是 | Claude 插件 manifest |
| `tests/` | 是 | 真实回归测试和契约测试 |
| `.github/workflows/` | 是 | CI 质量门 |
| `integrations/` | 否 | 转换器按需创建的可再生输出，已整体忽略 |

## 本地状态目录

这些目录不是源码，不应该提交：

- `.opc/`
- `.omx/`
- `.claude/`
- `integrations/`
- `.manual_verify/`
- `.pytest_tmp/`
- `.test_tmp/`
- `pytest-cache-files-*/`

其中 `.opc/` 和 `.omx/` 在运行 SuperOPC / OMX 时可能自动重新生成。

## 架构契约

SuperOPC 的核心契约是：

```text
Command -> Dispatcher Skill -> Agent Workflow -> Atomic Skill / references
```

- command 只做薄入口。
- dispatcher skill 只负责识别场景并派发 agent。
- agent 是完整 workflow 的事实源。
- scripts 是真实可执行 runtime。
- references/rules/templates 是 agent 和 runtime 使用的支持层。

## 推荐给朋友怎么说

推荐方式要准确：

> SuperOPC 目前是一个本地插件源仓库，不是已经发布到公开 marketplace 的一键安装包。可以克隆仓库后用 `scripts/convert.py` 生成 Codex / Claude Code / Cursor 等运行时包；在 Codex 中要真实执行 agent workflow，需要设置 `SUPEROPC_AGENT_RUNTIME=codex-exec`。

## 当前验证基线

本仓库的核心验证命令是：

```bash
python scripts/run_pytest.py tests/ -v
python scripts/verify_command_contract.py
python scripts/build_skill_registry.py --check
python scripts/opc_health.py --cwd . --target repo --json
```
