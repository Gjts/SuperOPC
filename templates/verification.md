# VERIFICATION.md 模板

> 用于 `.opc/phases/XX-name/{phase}-VERIFICATION.md` — 阶段级验证证据与质量门结果。

---

## 文件模板

```markdown
---
phase: XX-name
verification: XX-VERIFICATION
verified-from:
  - plan: XX-01
    requirements: [REQ-01]
  - plan: XX-02
    requirements: [REQ-02]
status: [pass / warn / fail]
requirements-verified: [REQ-01, REQ-02]
regression-impact: [受影响阶段/路径]
claim-sources: [代码文件、测试文件、截图、外部资料]
completed: YYYY-MM-DD
---

# 阶段 [X]：[名称] 验证

**[一句话说明本阶段交付物已验证的范围与结论]**

## must_haves 验证

### truths
- [ ] [truth 1] — [证据]
- [ ] [truth 2] — [证据]

### artifacts
- [ ] `path/to/file` 存在且非空
- [ ] `path/to/another` 含真实实现

### key_links
- [ ] [连接关系 1] — [证据]
- [ ] [连接关系 2] — [证据]

## 四层验证

### Exists
- [ ] [存在性检查]

### Substantive
- [ ] [实质性检查]

### Wired
- [ ] [接线检查]

### Functional
- [ ] [功能检查]

## Nyquist 采样
- 总文件数：[N]
- 采样策略：[全量 / 50% / 30%]
- 关键路径样本：[文件列表]
- 随机样本：[文件列表]

## 节点修复记录
- [无 / RETRY：说明 / DECOMPOSE：说明 / PRUNE：说明]

## 回归结果
- 自动化测试：[运行内容与结果]
- 人工验证：[操作与结果]
- 前序阶段影响：[无 / 具体说明]
- Schema drift：[无 / 已检查 / 待补迁移]

## 声明溯源
- 需求来源：[REQ-ID 列表]
- 代码证据：[关键文件 / 提交]
- 验证证据：[测试、截图、手工步骤、外部资料]
- 未验证声明：[如有，明确列出]
```

---

## 使用指南

### 目的
- 为阶段完成提供独立于 SUMMARY 的验证证据
- 支持 requirements coverage / regression / traceability / schema drift 检查
- 为 `/opc-health` 和后续 CI 提供稳定输入

### 何时创建
- 阶段所有计划完成后
- SUMMARY 草稿完成后
- 发布 / transition 之前

### 最低要求
- `requirements-verified` 不可为空
- 必须至少填写一项自动化测试或人工验证
- 必须补齐声明溯源区块
- 如果存在修复循环，必须记录 RETRY / DECOMPOSE / PRUNE
