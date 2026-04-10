# Security Policy

## 安全原则

SuperOPC 采用**建议性优先、关键风险阻断**的安全策略：

1. **纵深防御** — 多层检查，不依赖单一防线
2. **建议性优于强制性** — 大多数安全措施是警告而非阻止
3. **只在高风险场景阻止** — 例如绕过 hook 或疑似密钥泄露
4. **不阻止合法操作** — 安全检查不应干扰正常开发工作流
5. **透明** — 所有安全检查的逻辑对用户可见

## 当前内置安全措施

### Hooks 层

| 钩子 | 当前行为 |
|------|---------|
| `block-no-verify` | **阻止**包含 `--no-verify` 的 git 命令 |
| `commit-quality` | 检查 `git commit -m` 的 Conventional Commits 格式，并扫描 commit message 中的疑似密钥 |
| `prompt-injection-scan` | 对将要写入的内容做提示注入模式检测（建议性，不阻止） |
| `config-protection` | 当修改 linter / formatter / editor 配置文件时给出提醒 |
| `read-before-edit` | 提醒先读后改，降低基于过期上下文编辑的风险 |
| `state-file-lock` | 对 `.opc/STATE.md` / `.planning/STATE.md` 写入冲突给出建议性锁提示 |
| `command-audit-log` | 记录命令审计日志到 `.opc/audit.log` |
| `console-log-warn` | 检测编辑内容中的常见 debug 语句并提醒清理 |
| `session-summary` | 在会话结束时落盘最小会话摘要 |

### 当前检测模式

- **密钥泄露**
  - OpenAI key：`sk-...`
  - GitHub PAT：`ghp_...`
  - AWS Access Key：`AKIA...`
  - 以及部分高熵长字符串模式
- **提示注入**
  - `ignore previous instructions`
  - `you are now`
  - `disregard previous`
  - 零宽字符、异常 BOM 等隐藏字符模式
- **调试残留**
  - `console.log(...)`
  - `console.debug(...)`
  - `debugger;`
  - 常见 `print(...)` 调试输出
- **配置弱化风险**
  - `.eslintrc*`
  - `eslint.config.*`
  - `.prettierrc*`
  - `prettier.config.*`
  - `tsconfig*.json`
  - `biome.json*`
  - `.editorconfig`

## 重要说明

当前安全层以 **hook + 规则 + 审查流程** 为主，而不是集中式安全引擎。  
这意味着：

- 某些检查只覆盖命令文本或待写入内容，不扫描整个仓库历史
- 某些检查是建议性提醒，不会强制阻止操作
- `commit-quality` 当前主要检查 **commit message**，并不等价于完整 staged diff 扫描
- `session-summary` 当前保存的是**最小会话摘要**，不是完整行为取证日志

如果你需要更强的仓库级扫描，建议结合专用安全工具、CI 扫描和人工审计一起使用。

## 报告安全问题

如果你发现安全问题：

1. **不要**在公开 Issue 中直接披露可利用细节
2. 先通过仓库维护渠道私下联系维护者
3. 提供问题类型、影响范围、复现步骤、建议修复方案
4. 如果仓库尚未提供专用安全联系方式，请先使用仓库主页上的维护者联系入口

## 负责任披露

- 修复后可公开致谢报告者
- 严重问题应发布安全说明或变更记录
- 修复应尽量以最小补丁方式发布，并同步更新相关文档

## 安全路线图

- **v0.2.0** — Hooks 安全层
- **v0.6.0** — Python 工具链统一，hook 行为与插件清单进一步收敛
- **v1.3.0** — 集中安全模块（路径遍历、shell 净化、Unicode 检测增强）
- **v1.3.0** — OWASP ASVS 1-3 级威胁模型验证命令
- **v2.0.0** — 更完整的安全审计与生态集成
