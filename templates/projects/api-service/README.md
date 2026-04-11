# API Service 模板

> .NET 8 + PostgreSQL — 高性能 API 服务模板

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| 框架 | .NET 8 Minimal API | 高性能 + AOT 友好 |
| ORM | Entity Framework Core 8 | Code-First + 迁移管理 |
| 数据库 | PostgreSQL 15 | JSONB + 全文搜索 + RLS |
| 认证 | JWT Bearer + ASP.NET Identity | 标准 OAuth2 流程 |
| 文档 | OpenAPI / Swagger | 自动生成 API 文档 |
| 部署 | Docker + Railway / Fly.io | 容器化部署 |

## 适用场景

- RESTful API 后端服务
- 微服务架构中的单个服务
- Mobile App 后端
- 第三方集成 API

## 使用方式

```bash
# 1. 初始化项目
/opc-start

# 2. 选择此模板

# 3. 创建 .NET 项目
dotnet new webapi -n MyApi --use-minimal-apis
cd MyApi
dotnet add package Npgsql.EntityFrameworkCore.PostgreSQL
dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
```

## 预配置内容

```
.opc/
  PROJECT.md          # API 服务项目定义
  REQUIREMENTS.md     # RESTful API 需求（CRUD/认证/分页/错误处理）
  ROADMAP.md          # 4 阶段路线图
  STATE.md            # 初始状态
  config.json         # API 服务工作流配置
```

## 推荐技能组合

| 阶段 | 技能 |
|------|------|
| 设计 | `api-design` → `architecture-decision-records` |
| 开发 | `dotnet-patterns` → `postgres-patterns` → `backend-patterns` |
| 测试 | `tdd` → `e2e-testing` |
| 部署 | `docker-patterns` → `deployment-patterns` |
| 安全 | `security-review` |

## 适配的规则

- `rules/csharp/` — .NET 8 编码规范
- `rules/common/security.md` — OWASP 安全基线
- `rules/common/patterns.md` — 设计模式

## 关键架构决策

1. **Minimal API** — 比 Controller 模式更精简，适合微服务
2. **Repository + Service 分层** — 关注点分离
3. **FluentValidation** — 声明式请求验证
4. **Global Exception Handler** — 统一错误响应格式
