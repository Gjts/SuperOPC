---
name: security-review
description: Use for security audits, OWASP review, auth/input/database changes, or pre-release hardening. Dispatcher only; delegates to opc-security-auditor.
id: security-review
type: dispatcher
tags: [security, owasp, audit, auth, injection, xss, csrf, hardening]
dispatches_to: opc-security-auditor
triggers:
  keywords: [安全审计, owasp, 安全审查, security, audit, 漏洞, 注入, injection, auth, 授权]
  phrases: ["安全审查", "security review", "发布前检查", "输入校验"]
version: 1.4.1
---
# security-review — 安全审查派发器
**触发：** 安全审计、发布前检查、认证授权、用户输入、第三方集成、数据库查询变更。
**宣布：** "我调用 security-review 技能，派发给 opc-security-auditor 做安全审计。"
## 派发
使用 Task 工具派发 `opc-security-auditor` agent。
- **输入：** 审查范围、变更摘要、风险上下文
- **输出：** 威胁模型、OWASP 清单结果、分级发现、SECURE / NEEDS FIX / CRITICAL RISK 判决
## 边界
- 本 skill 不执行审计 workflow
- 安全清单在 `references/security-checklist.md`
- workflow 唯一事实源是 `agents/opc-security-auditor.md`
