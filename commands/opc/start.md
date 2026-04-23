---
name: opc-start
description: Initialize a new one-person company project - dispatches workflow-modes skill to route init vs resume flows
---
# /opc-start
显式进入 project-init workflow。
## 动作
调用 `workflow-modes` skill，传入 `$ARGUMENTS`，并附加 `sub_scenario=project-init`。
`opc-orchestrator` 会根据 `.opc/` 是否存在决定初始化、恢复，或在新商业想法场景下转交 `business-advisory`。
## 参数
- `$ARGUMENTS` - 项目名、想法、约束或初始化说明
