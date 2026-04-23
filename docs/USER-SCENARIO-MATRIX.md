# SuperOPC 测试用户与场景矩阵

这份矩阵把“谁在用 SuperOPC”转成可执行测试画像。目标不是写一份市场文案，而是让每个用户入口都有明确的验证策略。

## 1. 运营观测者

- 角色：单人项目经营者，频繁查看项目健康度、进度和业务指标。
- 背景：每天多次进入仓库，但不一定在当前会话里改代码。
- 核心目标：快速判断项目是否可继续推进，哪里有风险，下一步该做什么。
- 关键命令：`/opc-health`、`/opc-dashboard`、`/opc-stats`
- 成功标准：命令能在无人工介入下给出结构化状态、指标和债务信息。
- 验证方式：真实 CLI JSON 回归。

## 2. 上下文整理者

- 角色：负责把想法、延后事项和跨会话线索快速落盘的人。
- 背景：常在需求模糊或暂时不执行时使用轻量入口做捕获。
- 核心目标：以最低摩擦创建或检索 thread、seed、backlog 条目。
- 关键命令：`/opc-thread`、`/opc-seed`、`/opc-backlog`
- 成功标准：创建模式写入单文件 markdown，列表模式保持只读，并且 stderr advisory 可见。
- 验证方式：真实 CLI JSON 回归。

## 3. 会话恢复型开发者

- 角色：频繁中断和恢复工作的开发者。
- 背景：经常跨天继续同一阶段，需要依赖 `.opc/STATE.md` 和 `HANDOFF.json` 恢复上下文。
- 核心目标：准确知道当前进度、可暂停、可恢复、可输出会话报告。
- 关键命令：`/opc-progress`、`/opc-pause`、`/opc-resume`、`/opc-session-report`
- 成功标准：暂停会写入交接数据，恢复能回填状态连续性，报告能汇总债务和建议动作。
- 验证方式：真实 CLI JSON 回归。

## 4. 研究与索引维护者

- 角色：需要同时维护 developer profile、市场洞察和代码情报的人。
- 背景：既关心用户/市场信息，也关心仓库结构和索引是否新鲜。
- 核心目标：记录个人偏好、生成本地 insights、查询 methodology、刷新与检索 intel。
- 关键命令：`/opc-profile`、`/opc-research`、`/opc-intel`
- 成功标准：profile 可记录/展示/导出；research 可离线消费 feed 和 methods；intel 可 refresh/status/query/validate/diff。
- 验证方式：真实 `bin/opc-tools` CLI 回归。

## 5. 受边界约束的自主推进者

- 角色：希望在明确边界内自动推进，但仍保留人工检查点的高级用户。
- 背景：会先用 progress/roadmap 确认范围，再进入 bounded autonomous 模式。
- 核心目标：让系统在安全前提下生成自主推进计划，并在需要时切换 interactive 模式。
- 关键命令：`/opc-autonomous`、`/opc-cruise`、`/opc-heartbeat`
- 成功标准：`autonomous` 路径能根据 blocker / validation debt / interactive 标志返回正确推荐动作。
- 验证方式：`/opc-autonomous` 走真实 CLI；`/opc-cruise` 和 `/opc-heartbeat` 走命令契约验证。

## 6. 工作流编排者

- 角色：通过 slash 命令驱动规划、实现、评审、发布、调试和业务分析的人。
- 背景：依赖 dispatcher skill -> agent workflow 契约，而不是直接调用本地脚本。
- 核心目标：确保 slash 入口始终正确路由，不发生“伪派发”或错误直调脚本。
- 关键命令：`/opc`、`/opc-start`、`/opc-plan`、`/opc-build`、`/opc-review`、`/opc-ship`、`/opc-debug`、`/opc-security`、`/opc-business`、`/opc-pause`、`/opc-resume`、`/opc-progress`、`/opc-session-report`
- 成功标准：命令文档满足 dispatcher / mixed / readonly 契约，且真实仓库 lint 通过。
- 验证方式：命令契约 lint 与现有 engine/convert 回归。

## 场景覆盖策略

- Runtime E2E：`health`、`dashboard`、`stats`、`thread`、`seed`、`backlog`、`progress`、`pause`、`resume`、`session-report`、`profile`、`research`、`intel`、`autonomous`
- Contract-only：`opc`、`start`、`plan`、`build`、`review`、`ship`、`debug`、`security`、`business`、`cruise`、`heartbeat`

## 对应自动化

- 画像与命令覆盖：`tests/test_user_scenarios.py`
- 命令契约：`scripts/verify_command_contract.py` 与 `tests/engine/test_verify_command_contract.py`
- 关键底层回归：`tests/test_session_workflow.py`、`tests/test_quality_system.py`、`tests/test_opc_research.py`、`tests/engine/test_intel_helpers.py`
