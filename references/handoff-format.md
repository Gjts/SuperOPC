# HANDOFF Format — 交接文件格式参考

`HANDOFF.json` 是 SuperOPC v0.8.0 的会话交接快照。

默认路径：`.opc/HANDOFF.json`

目标：**让下一次会话在最短时间内恢复真实上下文，而不是重新读一遍所有历史。**

---

## 核心原则

1. **短** — 只写恢复需要的信息
2. **真** — 只写当前事实，不写猜测
3. **稳** — 字段结构固定，便于脚本读取
4. **可审计** — 人类打开 JSON 也能快速理解
5. **与 STATE.md 对齐** — handoff 不是第二套状态系统

---

## 推荐字段

```json
{
  "version": "0.8.0",
  "updatedAt": "2026-04-11T10:30:00Z",
  "project": {
    "name": "project-name",
    "root": "/absolute/path/to/project"
  },
  "session": {
    "id": "optional-session-id",
    "mode": "implementing",
    "source": "manual-pause"
  },
  "location": {
    "phase": "2/5",
    "plan": "1/3",
    "status": "执行中"
  },
  "summary": {
    "completed": "...",
    "stopPoint": "...",
    "reasonForPause": "..."
  },
  "nextSteps": [
    "主下一步",
    "备选下一步 A"
  ],
  "blockers": [
    "..."
  ],
  "validationDebt": [
    "..."
  ],
  "resumeFiles": [
    ".opc/STATE.md",
    "src/example.ts"
  ],
  "notes": [
    "其他短备注"
  ]
}
```

---

## 字段说明

### `version`
- handoff 格式版本
- 便于未来演进字段结构

### `updatedAt`
- 最近一次更新时间
- 使用 ISO 8601 UTC 时间

### `project`
- `name`：项目名
- `root`：项目根目录，便于跨 cwd 恢复

### `session`
- `id`：可选，对应运行时 session id
- `mode`：当前工作模式，如 `planning` / `implementing` / `reviewing`
- `source`：来源，如 `manual-pause` / `auto-checkpoint`

### `location`
- 从 `STATE.md` 提炼的当前位置
- 推荐至少包含：`phase`、`plan`、`status`

### `summary`
- `completed`：本轮已完成的最重要内容
- `stopPoint`：具体停在哪里
- `reasonForPause`：为什么现在暂停

### `nextSteps`
- 数组第一个元素必须是**主下一步**
- 总数建议不超过 3 条

### `blockers`
- 影响继续执行的问题
- 没有就写空数组，不要省略字段

### `validationDebt`
- 尚未完成的验证工作
- 例如测试未跑、手工验证未做、接线未确认

### `resumeFiles`
- 下次恢复时最值得优先读取的文件
- 建议按优先级排序
- 路径应尽量可直接打开

### `notes`
- 只保留短备注
- 长分析应放回 `STATE.md`、`PROJECT.md` 或专门文档

---

## 必填与选填

### 必填
- `version`
- `updatedAt`
- `project`
- `location`
- `summary`
- `nextSteps`
- `blockers`
- `validationDebt`
- `resumeFiles`
- `notes`

### 选填
- `session.id`
- `session.mode`
- `session.source`

如果没有值：
- 数组使用 `[]`
- 对象字段保留结构，值写空字符串或最小默认值

---

## 写入规则

1. **pause 时写入**
   - 每次 `/opc-pause` 都应覆盖 `.opc/HANDOFF.json`
   - handoff 永远表示“最近一次可恢复检查点”

2. **resume 后可更新**
   - 如果恢复时发现 handoff 与现实不一致，应在下一次 pause 时修正

3. **不要当日志文件使用**
   - 历史时间线应交给 `.opc/sessions/`
   - handoff 只保留最新快照

4. **不要隐藏不确定性**
   - 如果实现未验证，必须写到 `validationDebt`
   - 如果 blocker 未解决，必须写到 `blockers`

---

## 与其他文件的边界

| 文件 | 作用 | 不该承担什么 |
|------|------|--------------|
| `.opc/STATE.md` | 活状态 | 不负责稳定 JSON 结构 |
| `.opc/HANDOFF.json` | 最近交接快照 | 不做长历史归档 |
| `.opc/sessions/*.json` | 会话事件时间线 | 不做人工整理摘要 |
| `.opc/ROADMAP.md` | 阶段和计划进度 | 不记录细粒度暂停原因 |

---

## 质量检查清单

写完 `HANDOFF.json` 后，至少确认：
- [ ] 读一次就知道当前停在哪里
- [ ] 主下一步只有一个最优先动作
- [ ] blockers 已列清楚
- [ ] validation debt 已显式写出
- [ ] 恢复文件真实存在
- [ ] 内容没有复制整段日志或无关历史

---

## 模板

参考：`templates/handoff.json`
