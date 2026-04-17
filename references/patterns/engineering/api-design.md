---
name: api-design
description: Use when designing new API endpoints, reviewing API contracts, adding pagination/filtering, or planning versioning. Covers RESTful and GraphQL patterns for production APIs.
---

## API 设计模式

**宣布：** "我正在使用 api-design 技能来设计 API。"

## 何时激活

- 设计新 API 端点
- 审查现有 API 契约
- 添加分页、过滤、排序
- 实现 API 错误处理
- 规划 API 版本策略
- 构建面向外部的 API

## RESTful 设计

### URL 结构

```
# 资源用名词、复数、小写、kebab-case
GET    /api/v1/users
GET    /api/v1/users/:id
POST   /api/v1/users
PUT    /api/v1/users/:id       # 全量替换
PATCH  /api/v1/users/:id       # 部分更新
DELETE /api/v1/users/:id

# 子资源表示从属关系
GET    /api/v1/users/:id/orders
POST   /api/v1/users/:id/orders

# 不能映射到 CRUD 的操作（谨慎使用动词）
POST   /api/v1/orders/:id/cancel
POST   /api/v1/auth/login
```

### HTTP 方法语义

| 方法 | 幂等 | 安全 | 用途 |
|------|------|------|------|
| GET | ✓ | ✓ | 读取资源 |
| POST | ✗ | ✗ | 创建资源 |
| PUT | ✓ | ✗ | 全量替换 |
| PATCH | ✗ | ✗ | 部分更新 |
| DELETE | ✓ | ✗ | 删除资源 |

### 状态码

```
# 成功
200 OK              — GET/PUT/PATCH 成功
201 Created         — POST 创建成功（Location 头）
204 No Content      — DELETE 成功

# 客户端错误
400 Bad Request     — 请求体验证失败
401 Unauthorized    — 未认证
403 Forbidden       — 已认证但无权限
404 Not Found       — 资源不存在
409 Conflict        — 状态冲突（重复创建）
422 Unprocessable   — 业务逻辑验证失败
429 Too Many        — 速率限制

# 服务端错误
500 Internal Error  — 未预期的服务器错误
503 Service Unavail — 服务暂时不可用
```

## 统一响应格式

```json
// 成功（单资源）
{
  "data": { "id": "123", "email": "user@example.com" },
  "meta": { "request_id": "req_abc123" }
}

// 成功（列表 + 分页）
{
  "data": [...],
  "pagination": {
    "total": 100,
    "page": 1,
    "per_page": 20,
    "total_pages": 5
  }
}

// 错误
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Validation failed",
    "details": [
      { "field": "email", "message": "Invalid email format" }
    ]
  }
}
```

## 分页模式

### Offset 分页（简单、适合小数据集）
```
GET /api/v1/users?page=2&per_page=20
```

### Cursor 分页（适合大数据集、实时数据）
```
GET /api/v1/users?cursor=eyJpZCI6MTIzfQ&limit=20

// 响应
{
  "data": [...],
  "pagination": {
    "next_cursor": "eyJpZCI6MTQzfQ",
    "has_more": true
  }
}
```

## 版本策略

```
# URL 路径版本（推荐一人公司）
/api/v1/users
/api/v2/users

# 规则
- v1 永远保持向后兼容
- 破坏性变更 → v2
- 同时支持 v1 和 v2 至少 6 个月
- 弃用 → Sunset 头 + 文档公告
```

## GraphQL 模式

```graphql
# 查询用 Query，变更用 Mutation
type Query {
  user(id: ID!): User
  users(filter: UserFilter, pagination: PaginationInput): UserConnection!
}

type Mutation {
  createUser(input: CreateUserInput!): CreateUserPayload!
  updateUser(id: ID!, input: UpdateUserInput!): UpdateUserPayload!
}

# Relay-style 分页
type UserConnection {
  edges: [UserEdge!]!
  pageInfo: PageInfo!
  totalCount: Int!
}
```

## 一人公司 API 清单

- [ ] 统一响应格式（data + error + pagination）
- [ ] 所有端点需认证（JWT / API Key）
- [ ] 输入验证（Zod / FluentValidation / Pydantic）
- [ ] 速率限制（按 IP 或用户）
- [ ] CORS 配置
- [ ] OpenAPI/Swagger 文档自动生成
- [ ] 错误码注册表（避免魔法字符串）

## 压力测试

### 高压场景
- 先写接口实现，之后再补 API 约定。

### 常见偏差
- 接口路径、状态码和数据契约随手定。

### 使用技能后的纠正
- 先定义资源模型、契约和错误语义，再写实现。

