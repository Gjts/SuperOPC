# [项目名称] — API Service

## 这是什么

为 [客户端/前端/移动端] 提供数据和业务逻辑的 RESTful API 服务。
使用 .NET 8 Minimal API + PostgreSQL，提供 [核心领域] 的 CRUD 和业务流程。

## 核心价值

提供稳定、高性能、文档完善的 API，使前端/移动端可以专注于用户体验。

## 需求

### 已验证

（尚无 — 先发布后验证）

### 活跃

- [ ] RESTful API 覆盖核心业务实体的 CRUD
- [ ] JWT 认证和基于角色的授权
- [ ] 请求验证和统一错误响应
- [ ] 分页、排序、筛选的标准化查询
- [ ] OpenAPI 文档自动生成
- [ ] 数据库迁移可追溯

### 超范围

- GraphQL — v1 仅提供 REST
- 实时推送 — v1 用轮询，后续考虑 SignalR
- 多数据库支持 — v1 仅 PostgreSQL

## 背景

- 技术栈：.NET 8 + EF Core 8 + PostgreSQL 15
- 部署目标：Docker 容器 → Railway / Fly.io / Azure Container Apps

## 约束

- **性能**: P99 延迟 < 200ms（标准 CRUD）
- **安全**: OWASP Top 10 合规
- **兼容性**: .NET 8 LTS
- **可观测性**: 结构化日志 + Health Check

## 关键决策

| 决策 | 理由 | 结果 |
|------|------|------|
| Minimal API 而非 Controller | 代码更简洁，AOT 友好 | — 待定 |
| EF Core Code-First | 迁移可追溯，类型安全 | — 待定 |
| PostgreSQL 而非 SQL Server | 开源 + JSONB + 成本低 | — 待定 |

---
*最后更新：[日期]，项目初始化*
