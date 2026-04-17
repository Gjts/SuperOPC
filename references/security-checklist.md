# 安全审查清单（OWASP Top 10 对标）

> 本参考手册是 `agents/opc-security-auditor` 的评审清单来源。agent 通过
> "参考 `references/security-checklist.md`" 引用，不内联复制。
> 原内容来自已删除的 `skills/engineering/security-review/SKILL.md`。

## 何时引用

- 代码审查中发现安全相关代码
- 发布前安全检查
- 处理用户输入的新功能
- 认证 / 授权变更
- 第三方集成
- 数据库查询变更
- opc-reviewer 的 **Deep** 级审查强制调用本清单

## OWASP Top 10 检查清单

### A01：访问控制失效

- [ ] 每个端点都有认证检查？
- [ ] 用户只能访问自己的数据？（水平越权）
- [ ] 角色权限正确实施？（垂直越权）
- [ ] API 端点与前端路由权限一致？
- [ ] 敏感操作有二次确认？

### A02：密码学失败

- [ ] 密码使用 bcrypt / argon2 哈希？（不是 MD5 / SHA）
- [ ] 敏感数据传输使用 TLS？
- [ ] API Key / Token 不在日志中？
- [ ] 数据库中敏感字段加密？

### A03：注入

- [ ] SQL 查询使用参数化 / ORM？（无字符串拼接）
- [ ] 用户输入在渲染前转义？（XSS）
- [ ] 命令执行使用安全 API？（无 shell 拼接）
- [ ] LDAP / NoSQL 查询参数化？

### A04：不安全设计

- [ ] 业务逻辑有速率限制？
- [ ] 敏感操作有事务保护？
- [ ] 批量操作有限制？
- [ ] 错误信息不泄露内部细节？

### A05：安全配置错误

- [ ] 生产环境关闭 debug 模式？
- [ ] CORS 限制允许的源？
- [ ] 安全响应头设置？（CSP / X-Frame / HSTS）
- [ ] 默认密码 / 凭证已更改？
- [ ] 不必要的端口 / 服务已关闭？

### A06：脆弱和过时组件

```bash
# 检查依赖漏洞
npm audit
pip-audit
dotnet list package --vulnerable
```

- [ ] 至少每月运行一次依赖审计
- [ ] 高危 CVE 在 7 天内修复
- [ ] 使用 dependabot / renovate 自动 PR

### A07：认证失败

- [ ] 登录失败有速率限制？
- [ ] 密码强度要求？
- [ ] Session 超时配置？
- [ ] JWT 使用短有效期 + 刷新令牌？

### A08：软件和数据完整性

- [ ] CI / CD 流水线安全？（无 secret 泄露到日志）
- [ ] 第三方脚本使用 SRI 哈希？
- [ ] 部署包签名验证？

### A09：日志和监控不足

- [ ] 认证事件有日志？
- [ ] 敏感操作有审计日志？
- [ ] 日志不包含敏感数据？
- [ ] 异常行为有告警？

### A10：SSRF

- [ ] 服务端请求的 URL 白名单验证？
- [ ] 内网地址过滤？（127.0.0.1 / 10.x / 169.254.x）
- [ ] DNS rebinding 防护？

## 密钥泄露模式（自动扫描）

```
OpenAI:    sk-[a-zA-Z0-9]{20,}
GitHub PAT: ghp_[a-zA-Z0-9]{36}
AWS:       AKIA[A-Z0-9]{16}
Stripe:    sk_live_[a-zA-Z0-9]+
Supabase:  eyJ[a-zA-Z0-9_-]+
通用密码:  password\s*=\s*['"][^'"]+['"]
```

## 审查报告格式

```markdown
## 安全审查报告

**审查范围：** [文件 / 模块 / 功能]
**日期：** [YYYY-MM-DD]
**严重级别分布：** 🔴 Critical: N | 🟠 High: N | 🟡 Medium: N | 🔵 Low: N

### 发现

#### [SEVERITY] FINDING-01: [标题]
- **位置：** `path/to/file.ts:123`
- **OWASP：** A03 注入
- **描述：** [具体问题]
- **影响：** [攻击者可以做什么]
- **修复：** [具体修复建议 + 代码示例]

### 判决: SECURE / NEEDS FIX / CRITICAL RISK
```

## 一人公司安全优先级

1. **认证和授权**（最先做）
2. **输入验证**（防注入）
3. **密钥管理**（环境变量 + `.env.example` 占位）
4. **依赖审计**（自动化）
5. **日志和监控**（出事后能查）

## 关联

- `agents/opc-security-auditor.md` — 安全审查 workflow 持有者
- `agents/opc-reviewer.md` — Deep 级审查委派本清单
- `rules/common/security.md` — 通用安全硬规则
- `rules/typescript/security.md` / `rules/csharp/security.md` — 语言特定
