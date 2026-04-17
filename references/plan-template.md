# PLAN.md 标准模板

SuperOPC 的 PLAN.md 使用 XML + Markdown 混合结构。`<opc-plan>` 包裹的主体
会被 `scripts/engine/dag_engine.py` 直接解析，用于波次调度和任务派发。

## 完整骨架

~~~markdown
# [功能名称] 实施计划

<opc-plan>
  <metadata>
    <goal>[一句话目标]</goal>
    <spec-url>[设计规格链接]</spec-url>
    <estimated-time>[总耗时估算]</estimated-time>
  </metadata>

  <waves>
    <wave id="1" description="可并发执行的首层无依赖任务">
      <task id="1.1">
        <title>[小标题]</title>
        <file>path/to/file</file>
        <action>[具体做什么]</action>
        <test-expectation>[单测应该验证什么]</test-expectation>
        <completion-gate>[怎么知道做完了]</completion-gate>
      </task>
      <task id="1.2">
        ...
      </task>
    </wave>

    <wave id="2" description="依赖第一波的任务">
      <task id="2.1" depends_on="1.1,1.2">
         ...
      </task>
    </wave>
  </waves>
</opc-plan>

## OPC Plan Check
[由 opc-plan-checker 填写]

## OPC Assumptions Analysis
[由 opc-assumptions-analyzer 填写]

## OPC Pre-flight Gate

- plan-check: APPROVED
- assumptions: PASS
- ready-for-build: true
~~~

## 字段语义

| 字段 | 必填 | 说明 |
|---|---|---|
| `<metadata>.goal` | 是 | 一句话概括这份 PLAN 要交付什么 |
| `<metadata>.spec-url` | 建议 | 指向 `docs/specs/` 下的设计规格，便于溯源 |
| `<metadata>.estimated-time` | 建议 | 形如 `4-6h`，供一人公司排期 |
| `<wave>.id` | 是 | 从 `1` 开始递增，语义等同波次序号 |
| `<wave>.description` | 是 | 一句话说明这个波次在整体中的位置 |
| `<task>.id` | 是 | 层级编号 `<wave>.<seq>`，例如 `2.3` |
| `<task>.depends_on` | 否 | 跨波次或波次内部依赖，逗号分隔 task id |
| `<title>` | 是 | 动词短句，能被拎出来塞进 commit message |
| `<file>` | 是 | 具体文件路径；executor 不应该猜测修改哪里 |
| `<action>` | 是 | 要做的具体动作，控制在 1-5 行 |
| `<test-expectation>` | 是 | 没有测试期望的任务不能进入计划 |
| `<completion-gate>` | 是 | 可验证的完成信号；优先写可自动判定的条件 |

## 任务原子化原则

1. **2-5 分钟可完成** — 能在一个 AI 子代理的上下文中独立完成
2. **单一文件优先** — 跨多文件的任务应拆成更小的子任务
3. **测试驱动** — 每个任务都有可验证的 `<test-expectation>`
4. **可独立提交** — 每个 `<task>` 对应一个原子 commit

## 波次划分原则

- **波次内并行**：同一 `<wave>` 的任务彼此无依赖，可并行派发子代理
- **波次间串行**：`<wave id="N+1">` 依赖 `<wave id="N">` 的全部产物
- **依赖跨波次**：用 `depends_on="1.1,1.2"` 显式标注，不依赖 wave 顺序
- **波次数控制在 2-5** — 超过说明任务耦合过深，需重新拆分

## Pre-flight Gate 摘要

PLAN.md 末尾必须追加三段门控输出，作为 executor 的入口信号：

~~~markdown
## OPC Plan Check
[opc-plan-checker 输出: 8 维度校验结果]

## OPC Assumptions Analysis
[opc-assumptions-analyzer 输出: 技术/用户/商业/运维 假设清单]

## OPC Pre-flight Gate

- plan-check: APPROVED | REJECTED | NEEDS_REVISION
- assumptions: PASS | HIGH_RISK_UNMITIGATED
- ready-for-build: true | false
~~~

**`ready-for-build: true` 是 /opc-build 和 opc-executor 的唯一入口信号。**
缺失或为 false 时，executor 必须拒绝执行，回退到规划阶段。

## 关联文档

- `references/gates.md` — 四种门控 (Pre-flight / Revision / Escalation / Abort)
- `references/verification-patterns.md` — 四层验证模式
- `agents/opc-planner.md` — PLAN.md 的 workflow 持有者
- `agents/opc-plan-checker.md` — 8 维度规划校验器
- `agents/opc-assumptions-analyzer.md` — 假设提取器
