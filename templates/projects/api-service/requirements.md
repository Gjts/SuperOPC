# 需求：[项目名称] — API Service

**定义日期：** [日期]
**核心价值：** 稳定、高性能、文档完善的 API

## v1 需求

### 基础设施 (INFRA)

- [ ] **INFRA-01**: 项目骨架搭建（Minimal API + DI + Middleware）
- [ ] **INFRA-02**: EF Core + PostgreSQL 连接配置
- [ ] **INFRA-03**: 全局异常处理中间件（统一错误响应 RFC 7807）
- [ ] **INFRA-04**: 结构化日志（Serilog / Microsoft.Extensions.Logging）
- [ ] **INFRA-05**: Health Check 端点

### 认证 (AUTH)

- [ ] **AUTH-01**: JWT Bearer 认证配置
- [ ] **AUTH-02**: 用户注册端点（密码哈希 + 验证）
- [ ] **AUTH-03**: 登录端点（返回 Access Token + Refresh Token）
- [ ] **AUTH-04**: Token 刷新端点
- [ ] **AUTH-05**: 基于角色的授权策略

### 业务 API (API)

- [ ] **API-01**: 核心实体 CRUD 端点
- [ ] **API-02**: 请求验证（FluentValidation）
- [ ] **API-03**: 分页查询（offset/limit + 总数）
- [ ] **API-04**: 排序和筛选参数
- [ ] **API-05**: 资源关联和嵌套路由

### 文档 (DOC)

- [ ] **DOC-01**: OpenAPI/Swagger UI 配置
- [ ] **DOC-02**: API 端点注释和示例
- [ ] **DOC-03**: 认证流程文档

### 数据库 (DB)

- [ ] **DB-01**: 初始数据库迁移
- [ ] **DB-02**: 种子数据脚本
- [ ] **DB-03**: 索引优化（高频查询）

## v2 需求

### 高级功能

- **ADV-01**: 速率限制（Rate Limiting）
- **ADV-02**: 缓存层（Redis）
- **ADV-03**: 审计日志
- **ADV-04**: 文件上传（S3/Blob Storage）

## 超范围

| 功能 | 原因 |
|------|------|
| GraphQL | v1 仅 REST，降低复杂度 |
| 多数据库 | v1 仅 PostgreSQL |
| 微服务拆分 | v1 单体优先 |
| 实时推送 | 后续用 SignalR 补充 |

## 可追溯性

| 需求 | 阶段 | 计划 | Summary | Verification | 状态 |
|------|------|------|---------|--------------|------|
| INFRA-01 | 阶段 1 | - | - | - | 待定 |
| AUTH-01 | 阶段 2 | - | - | - | 待定 |
| API-01 | 阶段 3 | - | - | - | 待定 |
| DOC-01 | 阶段 3 | - | - | - | 待定 |
| DB-01 | 阶段 1 | - | - | - | 待定 |

**覆盖率：**
- v1 需求总数：18
- 已映射到阶段：18
- 未映射：0

---
*需求定义：[日期]*
