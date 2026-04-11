# Session Workflows — 会话工作流参考

SuperOPC v0.8.0 的会话管理工作流围绕四个命令展开：
- `/opc-progress`
- `/opc-pause`
- `/opc-resume`
- `/opc-session-report`

目标只有一个：**跨会话恢复时，读一次就知道在哪里、为什么停下、下一步做什么。**

---

## 设计原则

1. **STATE.md 是活状态**
   - 当前阶段、计划、状态、阻塞、待办、停止点都以 `.opc/STATE.md` 为主。

2. **HANDOFF.json 是恢复快照**
   - `.opc/HANDOFF.json` 保存最近一次人工整理的暂停摘要。
   - 它服务恢复，不承担长期归档职责。

3. **sessions/ 是时间线，不是决策源**
   - `.opc/sessions/*.json` 记录会话事件和时间戳。
   - 当 handoff 与 state 缺失细节时，可用来补充时间线。

4. **一个主下一步胜过多个模糊建议**
   - 输出应优先给出一个最值得马上执行的动作。

5. **验证欠债必须显式记录**
   - 未运行测试
   - 未完成人工验证
   - 已实现但尚未确认接线/功能

---

## 文件职责

| 文件 | 角色 | 何时读取 | 何时更新 |
|------|------|----------|----------|
| `.opc/STATE.md` | 项目活状态 | 每次 progress / pause / resume / report | 每个重要操作后 |
| `.opc/HANDOFF.json` | 恢复快照 | resume / report | pause 时 |
| `.opc/ROADMAP.md` | 阶段与计划位置 | progress / resume / report / autonomous | 阶段推进时 |
| `.opc/REQUIREMENTS.md` | 完成度和范围检查 | progress / report | 需求变化时 |
| `.opc/sessions/*.json` | 会话时间线 | progress / resume / report | 会话结束或检查点时 |
| `.opc/todos/` | 会话中捕获的后续事项 | progress / report | 发现新想法时 |

---

## `/opc-progress` 何时使用

适用场景：
- 开工前先对齐当前位置
- 想快速知道下一个未完成计划
- 需要看 blockers / todos / verification debt
- handoff 不完整，先看项目主状态

推荐读取顺序：
1. `.opc/STATE.md`
2. `.opc/ROADMAP.md`
3. `.opc/REQUIREMENTS.md`
4. 最新 `.opc/sessions/*.json`

推荐输出：
- 当前位置（phase / plan / status）
- 停止于 / 最近活动 / 恢复文件
- 完成度（phase / plan / requirements）
- blockers / todos / risky decisions
- 一个主下一步
- validation debt

---

## `/opc-pause` 何时使用

适用场景：
- 会话结束前
- 要切到另一项工作前
- 上下文接近过载，需要主动检查点
- 要把工作交给未来的自己或其他代理

最小暂停协议：
1. 更新 `.opc/STATE.md` 的会话连续性字段
2. 整理一个简短摘要
3. 写入 `.opc/HANDOFF.json`
4. 明确一个主下一步
5. 明确 blockers 与 validation debt

暂停时不要做的事：
- 不复制大段日志
- 不把所有想法都写进 handoff
- 不用模糊话术如“继续完善”
- 不隐去未验证实现

---

## `/opc-resume` 何时使用

适用场景：
- 新会话开始时
- 从中断位置恢复时
- 接收别的代理交接时
- 怀疑当前状态与记忆不一致时

推荐恢复顺序：
1. 读 `.opc/HANDOFF.json`
2. 读 `.opc/STATE.md`
3. 校验 `.opc/ROADMAP.md` 位置
4. 检查恢复文件是否存在
5. 如有必要，再读最新 `.opc/sessions/*.json`

恢复后的第一动作优先级：
1. 先解决 blocker
2. 再处理 validation debt
3. 然后执行主下一步

如果恢复材料冲突：
- 以当前文件系统中的最新事实为准
- 报告冲突点
- 必要时重写 handoff，避免下次继续漂移

---

## `/opc-autonomous` 何时使用

适用场景：
- 路线图边界已经明确
- 想连续推进一段已知范围，而不是每一步都重新确认
- 仍希望保留 blocker、validation debt 和人工检查点的停机条件

推荐读取顺序：
1. `.opc/STATE.md`
2. `.opc/ROADMAP.md`
3. `.opc/HANDOFF.json`（如果存在）
4. 当前恢复文件与最新 `.opc/sessions/*.json`

推荐输出：
- 当前执行窗口（`--from` / `--to` / `--only`）
- 当前是否适合自主推进，或应降级到 `/opc-discuss` / `/opc-progress`
- 一个主推荐命令
- 本轮自主推进的最小步骤序列
- blockers / validation debt / resume files

`/opc-autonomous` 不是独立状态系统；它依然依赖 `STATE.md`、`HANDOFF.json`、路线图位置和验证欠债信号来决定是否继续。

---

## `/opc-session-report` 何时使用

适用场景：
- 日结
- 阶段复盘
- 给未来会话留摘要
- 想看当前会话贡献而不是只看静态项目状态

推荐输出结构：
1. 时间范围 / 会话数 / 工具来源
2. 本轮完成事项
3. 当前停留位置
4. 进度变化
5. blockers / todos / risky decisions
6. validation debt / manual verification
7. 一个主下一步

`/opc-session-report` 偏总结；`/opc-pause` 偏交接。两者可以连续使用，但不应互相替代。

---

## Validation Debt 定义

以下情况都算 validation debt：
- 代码或文档已修改，但测试未跑
- 静态检查未跑
- 手工验证尚未完成
- 只验证了 Exists，没有验证 Substantive / Wired / Functional
- 路线图、状态、handoff 三者尚未重新对齐

建议记录格式：
- `未运行：unit tests`
- `未验证：手工点击主流程`
- `未确认：新命令是否已接入导出流程`

参考：`references/verification-patterns.md`

---

## 与上下文预算配合

当上下文使用率升高时：
- 先执行 `/opc-pause` 保存检查点
- 下次用 `/opc-resume` 恢复
- 若只需快速对齐，不必立刻 resume，可先 `/opc-progress`

这与 `references/context-budget.md` 的检查点策略一致：
- 长任务定期保存进度
- 避免在高上下文压力下继续无检查点推进

---

## 推荐最小闭环

### 开工
1. `/opc-progress`
2. 对齐主下一步

### 中途切换任务
1. `/opc-pause`
2. 切换任务
3. 回来时 `/opc-resume`

### 收工
1. `/opc-session-report`
2. `/opc-pause`

这样可以同时得到：
- 一个对人友好的会话总结
- 一个对恢复友好的 handoff 快照
