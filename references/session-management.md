# Session Management — 会话管理

v0.8.0 为 SuperOPC 增加跨会话连续性：暂停、恢复、进度查看、会话报告。

---

## 核心工件

### `.opc/HANDOFF.json`
人工整理的恢复检查点。目标是：**下一次会话读一次就知道从哪里继续。**

建议字段：
- `version`
- `updatedAt`
- `project`
- `session`
- `location`
- `summary`
- `nextSteps`
- `blockers`
- `validationDebt`
- `resumeFiles`
- `notes`

### `.opc/STATE.md`
项目活状态。`HANDOFF.json` 是会话级检查点，`STATE.md` 是项目级当前位置。

### `.opc/sessions/*.json`
由 stop hook 自动记录的最小会话时间线。

### `.opc/audit.log`
命令审计轨迹，可供会话报告引用。

---

## 生命周期

### Pause
1. 读取当前 `.opc` 状态
2. 生成 `HANDOFF.json`
3. 刷新 `STATE.md` 的：
   - 上次会话
   - 停止于
   - 恢复文件

### Resume
1. 优先读取 `HANDOFF.json`
2. 用 `STATE.md` 校验当前位置
3. 如果两者冲突，以最新事实为准
4. 刷新 `STATE.md` 的会话连续性字段，保持恢复入口最新
5. 给出单一主下一步

### Progress
输出当前位置、完成度、验证欠债和主下一步。

### Session Report
聚合 `HANDOFF.json`、session 文件、audit log 和当前状态，生成可读报告。

---

## 冲突规则

1. `STATE.md` 比 handoff 更新时，以 `STATE.md` 为准
2. handoff 缺失时，退回 `STATE.md` + `ROADMAP.md`
3. 恢复文件失效时，要明确提示，不静默忽略
4. blockers 未清理时，优先建议先解除阻塞

---

## 设计原则

- **读一次可恢复**：不要写成长篇日志
- **一个主下一步**：不要给过多平行建议
- **事实优先**：记录观察到的真实状态，不写猜测
- **项目状态与会话状态分离**：`STATE.md` 管项目，`HANDOFF.json` 管暂停点
