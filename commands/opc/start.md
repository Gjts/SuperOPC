---
name: opc-start
description: Initialize a new one-person company project with SuperOPC structure
---

# /opc-start — 初始化一人公司项目

## 流程

1. **收集项目信息**
   - 项目名称
   - 一句话描述（解决什么问题）
   - 目标用户
   - 技术栈偏好

2. **创建项目文件**
   - `PROJECT.md` — 项目愿景和定位
   - `REQUIREMENTS.md` — v1 需求清单
   - `ROADMAP.md` — 阶段路线图
   - `docs/` — 设计规格和计划目录

3. **初始化 SuperOPC 配置**
   - 确认 CLAUDE.md 存在
   - 确认 AGENTS.md 存在
   - 初始化 git（如果还没有）

4. **输出下一步建议**
   - 使用 `/opc-research` 做市场研究
   - 使用 `/opc-plan` 开始规划第一个功能
   - 使用 `/opc-build` 开始开发

## PROJECT.md 模板

```markdown
# [项目名称]

## 愿景
[一句话：为 [谁] 解决 [什么问题]]

## 目标用户
[具体的用户画像]

## 核心价值主张
[为什么用户选择你而不是替代方案]

## 技术栈
[选择的技术栈及理由]

## 成功指标
- [指标 1]
- [指标 2]
```
