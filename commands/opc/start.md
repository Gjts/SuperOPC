---
name: opc-start
description: Initialize a new one-person company project with SuperOPC structure
---
# /opc-start
项目初始化入口。
## 动作
调用 `planning` skill 或 `workflow-modes` skill，传入 `$ARGUMENTS`。
由 agent 澄清项目定位、目标用户、技术栈、初始需求和下一步路线图。
## 参数
- `$ARGUMENTS` — 项目名称、想法、约束或初始化说明
