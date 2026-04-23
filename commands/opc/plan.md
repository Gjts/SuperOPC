---
name: opc-plan
description: Plan a feature or phase - dispatches planning skill which owns the workflow
---
# /opc-plan
显式进入 planning workflow。
## 动作
调用 `planning` skill，传入 `$ARGUMENTS`。
涉及新产品或新商业想法时，`opc-planner` 会执行 Anti-Build-Trap；证据不足则改派 `business-advisory`。
## 参数
- `$ARGUMENTS` - 功能描述、约束或 spec 路径
