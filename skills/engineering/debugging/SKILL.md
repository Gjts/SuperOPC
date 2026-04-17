---
name: debugging
description: Use when encountering bugs, errors, unexpected behavior, or failing tests. Dispatcher only — delegates to opc-debugger agent for hypothesis-evidence-elimination investigation.
---

## 调试派发器

**这是 dispatcher skill。不包含 workflow，统一派发给 `opc-debugger` agent。**

## 触发场景

- 线上 bug / 生产环境异常
- 测试失败（单元 / 集成 / E2E）
- 非预期行为（UI 不对 / 接口返回错 / 数据不一致）
- 性能异常（慢查询 / 内存泄漏）
- 难以复现的间歇性问题

## 派发动作

```
Task(subagent_type="opc-debugger", description="bug-investigation", prompt="[预期行为 / 实际行为 / 错误消息 / 何时开始]")
```

opc-debugger 会执行四阶段根因调查：

1. **Phase 1 证据收集** —— 完整读错误信息 + 堆栈 + git 历史 + 数据流追踪
2. **Phase 2 形成假设** —— 具体可证伪；3+ 独立假设避免锚定
3. **Phase 3 测试假设** —— 一次一个变量，预测→测试→观察→结论
4. **Phase 4 评估与修复** —— 确认根因 → 先写失败测试（调用 `tdd` skill） → 单一修复 → 验证；≥3 次修复失败自动升级到架构讨论

## 铁律

1. **dispatcher 不执行调查** —— 所有证据收集和假设验证留给 opc-debugger
2. **没有根因，不写修复** —— 由 agent 强制执行
3. **一次只改一个变量** —— 由 agent 强制执行
4. **≥3 次修复失败自动质疑架构** —— 由 agent 触发 opc-planner 重评估

## 关联

- `agents/opc-debugger.md` —— workflow 持有者
- `skills/engineering/tdd/` —— 修复阶段调用的刚性原子技能
