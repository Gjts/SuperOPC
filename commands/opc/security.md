---
name: opc-security
description: Security audit — dispatches security-review skill which owns the workflow
---
# /opc-security — 安全审计入口
用户显式触发安全审计。等价于自然语言 "做个安全审计" / "查下有没有安全漏洞"。
## 动作
调用 `security-review` skill，传入 `$ARGUMENTS`。
security-review skill 会派发 `opc-security-auditor` agent 执行 OWASP Top 10 检查（注入 / 认证 / 密钥 / 配置 / 权限 / 日志 / SSRF / 反序列化 / 依赖 / 密码学）+ 输出威胁模型和修复建议。
## 入口要求
- 代码 / 架构 / 配置已基本稳定（不建议在重构进行中做全面审计）
- 大型审计建议先指定范围（某个模块 / 某个 API 表面）
## 参数
- `$ARGUMENTS` — 审计范围（文件 / 目录 / 模块名）或自然语言说明
