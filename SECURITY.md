# Security Policy

## 安全原则

SuperOPC 遵循**建议性优先**的安全策略：

1. **纵深防御** — 多层检查，不依赖单一防线
2. **建议性优于强制性** — 大多数安全措施是警告而非阻止
3. **不阻止合法操作** — 安全检查不应干扰正常开发工作流
4. **透明** — 所有安全检查的逻辑对用户可见

## 内置安全措施

### Hooks 层

| 钩子 | 检查内容 |
|------|---------|
| `block-no-verify` | 阻止绕过 git pre-commit hooks |
| `commit-quality` | 密钥/token 检测（OpenAI, GitHub PAT, AWS） |
| `prompt-injection-scan` | 提示注入模式检测（Unicode 隐形字符、指令覆盖） |
| `config-protection` | 防止 linter/formatter 配置被削弱 |

### 检测模式

- **密钥泄露**：OpenAI key (`sk-`)、GitHub PAT (`ghp_`)、AWS key (`AKIA`)
- **提示注入**：`ignore previous instructions`、`you are now`、零宽字符、BOM 异位
- **路径遍历**：文件路径验证（计划中 v1.3.0）

## 报告安全漏洞

如果你发现安全漏洞：

1. **不要**在公开 Issue 中报告
2. 发送邮件至项目维护者（见 README）
3. 描述漏洞类型、影响范围、复现步骤
4. 我们会在 48 小时内回复

## 负责任的披露

- 我们会在修复后公开致谢报告者
- 严重漏洞会发布安全公告
- 修复会以补丁版本发布

## 安全路线图

- **v0.2.0** — Hooks 安全层（当前）
- **v1.3.0** — 集中安全模块（路径遍历、shell 净化、Unicode 检测增强）
- **v1.3.0** — OWASP ASVS 1-3 级威胁模型验证命令
- **v2.0.0** — 完整安全审计
