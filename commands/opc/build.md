---
name: opc-build
description: Execute an approved PLAN.md — dispatches implementing skill which owns the workflow
---

# /opc-build — 执行入口

用户显式触发实现流程。等价于自然语言 "执行计划"。

## 动作

调用 `implementing` skill，传入 `$ARGUMENTS`（可选的 PLAN.md 路径）。

implementing skill 会派发 `opc-executor` agent 执行完整流程（入口门控 → 波次执行 → 双阶段审查 → 原子提交 → SUMMARY.md）。

## 入口要求

目标 PLAN.md 必须包含 `## OPC Pre-flight Gate` 且 `ready-for-build: true`。

## 参数

- `$ARGUMENTS` — 可选，指定要执行的 PLAN.md 路径；缺省时查找最新
