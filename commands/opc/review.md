---
name: opc-review
description: Trigger a comprehensive code review on recent changes
---

# /opc-review — 代码审查

## 流程

1. **确定审查范围**
   ```bash
   git diff main --name-only
   ```

2. **派发 opc-reviewer 代理**
   - 五维度审查
   - 输出审查报告

3. **根据结果行动**
   - 有严重问题 → 修复
   - 全部通过 → 建议 `/opc-ship`

## 参数
- `$ARGUMENTS` — 可选，指定审查范围（文件或分支）
