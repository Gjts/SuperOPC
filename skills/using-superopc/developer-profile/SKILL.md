---
name: developer-profile
description: Use when onboarding a new developer or when SuperOPC behavior feels misaligned with user preferences. Runs 8-dimension questionnaire and personalizes system behavior.
---

# 开发者画像 — 8 维度个性化引擎

根据开发者的工作风格自动调整 SuperOPC 的沟通、决策和交互方式。

## 适用时机

- **首次使用 SuperOPC** — `/opc-start` 自动触发
- **行为不匹配** — 用户说"太啰嗦"/"不够详细"/"别问了直接做"
- **显式刷新** — `/opc-profile --refresh`

## 8 维度模型

| # | 维度 | 选项 | 影响 |
|---|------|------|------|
| 1 | 沟通风格 | terse / balanced / verbose | 输出长度、列表 vs 段落 |
| 2 | 决策模式 | intuitive / analytical / consensus-seeking | 是否展示权衡分析 |
| 3 | 调试方式 | systematic / intuitive / log-driven | 调试流程选择 |
| 4 | UX 偏好 | minimalist / feature-rich / data-dense | UI 建议风格 |
| 5 | 技术栈亲和 | [自动检测] | 代码示例语言、框架推荐 |
| 6 | 摩擦触发 | [自动检测] | 避免令用户沮丧的模式 |
| 7 | 学习风格 | hands-on / conceptual / example-driven | 解释方式 |
| 8 | 解释深度 | brief / moderate / deep | 详细程度 |

## 画像获取流程

### 方式 1: 问卷（首次/刷新）

向用户提出 6 个快速选择题（技术栈和摩擦触发从交互自动检测）：

```
Q1: 你希望我的回复风格是？
    [A] 简洁直接，少废话  [B] 适度详细  [C] 充分解释每个决策

Q2: 做技术决策时，你更倾向？
    [A] 跟着感觉快速决定  [B] 看数据和对比再决定  [C] 讨论后一起决定

Q3: 遇到 bug 时，你通常？
    [A] 系统化缩小范围  [B] 凭直觉跳到可能的原因  [C] 先加日志看发生了什么

Q4: UI/UX 方面你偏好？
    [A] 极简，功能为王  [B] 功能丰富，什么都能做  [C] 数据密集，一屏看全

Q5: 学新东西时你更喜欢？
    [A] 直接动手做  [B] 先理解原理  [C] 看示例代码

Q6: 解释事情时你希望多详细？
    [A] 最短能理解就行  [B] 适当展开  [C] 完整深入
```

### 方式 2: 行为推断（持续）

从会话中自动推断：
- 频繁用 `/opc-quick` → communication_style: terse
- 频繁用 `/opc-plan` → decision_pattern: analytical
- 检测到的技术栈 → tech_stack_affinity
- 用户表达不满的模式 → friction_triggers

## 画像输出

存储位置: `~/.opc/USER-PROFILE.json`

画像注入方式：
1. `context_assembler.py` 读取画像 → 注入会话上下文
2. `decision_engine.py` 根据画像调整权重
3. 代理根据 `explanation_depth` 调整输出详细度

## 画像影响矩阵

| 维度值 | SuperOPC 行为调整 |
|--------|------------------|
| terse | 不显示过程解释，直接给结果和行动 |
| verbose | 展示决策原因、替代方案、权衡分析 |
| intuitive | 减少确认步骤，快速执行 |
| analytical | 每步展示数据支撑 |
| systematic | 调试时遵循假设→证据→排除流程 |
| log-driven | 调试时优先添加日志语句 |
| brief | 一行总结 |
| deep | 包含背景知识、原理、扩展阅读 |

## 关联

- `/opc-profile` — 查看/刷新画像
- `/opc-start` — 首次使用时触发画像问卷
- `scripts/engine/profile_engine.py` — 底层引擎
- `scripts/engine/context_assembler.py` — 画像注入
