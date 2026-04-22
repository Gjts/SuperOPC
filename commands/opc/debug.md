---
name: opc-debug
description: Investigate a bug — dispatches debugging skill which owns the workflow
---
# /opc-debug — 调试入口
用户显式触发调试流程。等价于自然语言 "有个 bug" / "这里报错了" / "测试失败"。
## 动作
调用 `debugging` skill，传入 `$ARGUMENTS`。
debugging skill 会派发 `opc-debugger` agent 执行四阶段根因分析（现象捕获 → 假设-证据-排除 → 定位根因 → 修复验证回归）。
## 入口要求
- 有具体的错误信息、日志、失败测试或可复现步骤
- 若信息不足，opc-debugger 会先要求补充
## 参数
- `$ARGUMENTS` — 错误信息、测试名、日志片段、或自然语言问题描述
