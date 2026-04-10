# TDD Reference — 测试驱动开发参考

TDD 关乎设计质量，而非覆盖率指标。RED-GREEN-REFACTOR 循环迫使你在实现前思考行为，产出更干净的接口和更可测试的代码。

**原则：** 如果你能在写 `fn` 之前描述 `expect(fn(input)).toBe(output)`，TDD 就能改善结果。

---

## 何时使用 TDD

**适合 TDD：**
- 有明确输入/输出的业务逻辑
- API 端点（请求/响应契约）
- 数据转换、解析、格式化
- 验证规则和约束
- 算法
- 状态机和工作流
- 工具函数

**跳过 TDD：**
- UI 布局和样式
- 配置变更
- 胶水代码
- 一次性脚本
- 简单 CRUD（无业务逻辑）
- 探索性原型

**启发式：** 能写 `expect(fn(input)).toBe(output)` 吗？
→ 能：使用 TDD
→ 不能：标准开发，需要时补测试

---

## RED-GREEN-REFACTOR 循环

### RED — 写失败测试
1. 创建测试文件
2. 写描述预期行为的测试
3. 运行测试 — 必须**失败**
4. 如果通过：功能已存在或测试有误，调查
5. 提交：`test(scope): add failing test for [feature]`

### GREEN — 实现通过
1. 写最小代码使测试通过
2. 不追求巧妙，只追求通过
3. 运行测试 — 必须**通过**
4. 提交：`feat(scope): implement [feature]`

### REFACTOR — 重构（如需）
1. 如有明显改进则清理实现
2. 运行测试 — 必须仍然**通过**
3. 有变更才提交：`refactor(scope): clean up [feature]`

**结果：** 每个 TDD 计划产出 2-3 个原子提交。

---

## 好测试 vs 坏测试

| 好 | 坏 |
|---|---|
| 测试行为（"返回格式化日期"） | 测试实现（"调用 formatDate 帮助函数"） |
| 每个测试一个概念 | 一个测试检查所有边界情况 |
| 描述性名称 | `test1`, `handles error` |
| 测试公共 API | Mock 内部实现 |

---

## 框架设置

| 项目 | 框架 | 安装 |
|------|------|------|
| Node.js | Vitest | `npm install -D vitest` |
| Node.js | Jest | `npm install -D jest ts-jest` |
| Python | pytest | `pip install pytest` |
| Go | testing | 内置 |
| Rust | cargo test | 内置 |
| .NET | xUnit | `dotnet add package xunit` |

---

## 上下文预算

TDD 计划目标 **~40% 上下文使用率**（低于标准计划的 ~50%）。

原因：
- RED 阶段：写测试、运行、调试
- GREEN 阶段：实现、运行、迭代
- REFACTOR 阶段：修改、运行、验证

每个阶段都涉及读文件、运行命令、分析输出。来回固有地比线性任务执行更重。
