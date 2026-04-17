---
name: security-review
description: Use when reviewing code for security vulnerabilities, conducting security audits, hardening against OWASP Top 10, or before production release. Dispatcher only — delegates to opc-security-auditor agent.
---

## 安全审查派发器

**这是 dispatcher skill。不包含 workflow，统一派发给 `opc-security-auditor` agent。**

## 触发场景

- 代码审查中发现安全相关代码
- 发布前安全检查
- 处理用户输入的新功能
- 认证 / 授权变更
- 第三方集成
- 数据库查询变更
- opc-reviewer 的 **Deep** 级审查要求安全子审

## 派发动作

```
Task(subagent_type="opc-security-auditor", description="security-audit", prompt="[审查范围 + 变更摘要]")
```

opc-security-auditor 会：

1. 做轻量威胁模型（资产识别 → 攻击面枚举）
2. 自动扫描密钥泄露 / 注入漏洞 / 配置错误
3. 按 `references/security-checklist.md` 逐项完成 **OWASP Top 10 A01-A10** 清单
4. 输出分级报告（🔴 Critical / 🟠 High / 🟡 Medium / 🔵 Low）+ 判决（SECURE / NEEDS FIX / CRITICAL RISK）

## 铁律

1. **dispatcher 不执行 workflow** —— 所有审查动作留给 opc-security-auditor
2. **密钥泄露或认证缺陷阻止发布** —— 由 auditor 输出 CRITICAL RISK 判决触发
3. **一人公司优先级：** 认证授权 > 输入验证 > 密钥管理 > 依赖审计 > 日志监控

## 关联

- `agents/opc-security-auditor.md` —— workflow 持有者
- `references/security-checklist.md` —— OWASP Top 10 完整清单
- `rules/common/security.md` —— 通用安全硬规则
