---
name: debugging
description: Use for bugs, errors, unexpected behavior, failing tests, or performance anomalies. Dispatcher only; delegates to opc-debugger.
id: debugging
type: dispatcher
tags: [debugging, bug, error, diagnosis, troubleshooting, root-cause]
dispatches_to: opc-debugger
triggers:
  keywords: [bug, 调试, 异常, 错误, 失败, debug, 堆栈, stack, panic, 报错]
  phrases: ["修一下 bug", "为什么错了", "测试失败", "复现不出来"]
version: 1.4.1
---
# debugging — 调试派发器
**触发：** bug、异常、测试失败、非预期行为、性能问题、难复现问题。
**宣布：** "我调用 debugging 技能，派发给 opc-debugger 做根因调查。"
## 派发
使用 Task 工具派发 `opc-debugger` agent。
- **输入：** 预期行为、实际行为、错误消息、复现步骤、开始时间
- **输出：** 假设-证据-排除记录、根因、修复或升级建议
## 边界
- 本 skill 不执行调查、不写修复
- 修复阶段由 `opc-debugger` 调用 `tdd`
- workflow 唯一事实源是 `agents/opc-debugger.md`
