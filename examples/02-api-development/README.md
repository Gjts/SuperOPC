# 示例 2：用 SuperOPC 开发 API 服务

> 演示 .NET 8 API 服务从设计到部署的完整工作流

## 场景

你要为一个任务管理应用构建 RESTful API 后端：**TaskFlow API** — 提供任务的 CRUD、分类、优先级和截止日期管理。

## 工作流演示

### 第一步：初始化并选择模板

```
/opc-start
```

选择 `api-service` 模板，SuperOPC 会生成预配置的 `.opc/` 结构。

### 第二步：API 设计先行

```
/opc-plan TaskFlow RESTful API 设计
```

SuperOPC 使用 `api-design` 技能规划 API：

```
## API 端点设计

### Tasks
GET    /api/v1/tasks              # 列表（分页+筛选+排序）
POST   /api/v1/tasks              # 创建
GET    /api/v1/tasks/{id}         # 详情
PUT    /api/v1/tasks/{id}         # 更新
DELETE /api/v1/tasks/{id}         # 删除
PATCH  /api/v1/tasks/{id}/status  # 状态变更

### Categories
GET    /api/v1/categories         # 列表
POST   /api/v1/categories         # 创建

### Auth
POST   /api/v1/auth/register      # 注册
POST   /api/v1/auth/login         # 登录
POST   /api/v1/auth/refresh       # 刷新 Token
```

### 第三步：数据库设计

```
/opc-plan 数据库 Schema 和迁移
```

SuperOPC 使用 `database-migrations` + `postgres-patterns` 技能：

```csharp
// Entities
public class TaskItem
{
    public Guid Id { get; set; }
    public string Title { get; set; } = string.Empty;
    public string? Description { get; set; }
    public TaskPriority Priority { get; set; }
    public TaskStatus Status { get; set; }
    public DateTime? DueDate { get; set; }
    public Guid CategoryId { get; set; }
    public Category Category { get; set; } = null!;
    public Guid UserId { get; set; }
    public DateTime CreatedAt { get; set; }
    public DateTime UpdatedAt { get; set; }
}
```

### 第四步：TDD 开发

```
/opc-build
```

SuperOPC 执行 TDD 循环：

```
RED   → 写失败测试: POST /api/v1/tasks 返回 201
GREEN → 实现最小代码让测试通过
REFACTOR → 提取 Service 层，添加 FluentValidation
```

每个端点都经过：
1. 单元测试（Service 层）
2. 集成测试（WebApplicationFactory）
3. 代码审查（`opc-reviewer`）

### 第五步：安全审计

```
/opc-build    # 在阶段转换时自动触发
```

`opc-security-auditor` 检查：
- JWT 配置（密钥长度、过期时间）
- SQL 注入防护（EF Core 参数化查询）
- CORS 策略
- 输入验证覆盖率
- 错误消息不泄露敏感数据

### 第六步：Docker 化部署

```
/opc-plan Docker 化和 CI/CD 配置
```

使用 `docker-patterns` + `deployment-patterns` 技能：

```dockerfile
# 多阶段构建
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY . .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:8.0
WORKDIR /app
COPY --from=build /app .
EXPOSE 8080
ENTRYPOINT ["dotnet", "TaskFlow.Api.dll"]
```

## 关键技能使用

| 技能 | 场景 |
|------|------|
| `api-design` | RESTful 端点设计 + 版本策略 |
| `dotnet-patterns` | Minimal API + DI + Middleware |
| `postgres-patterns` | 索引优化 + 查询调优 |
| `database-migrations` | EF Core Code-First 迁移 |
| `backend-patterns` | Repository + Service 分层 |
| `tdd` | 每个端点先写测试 |
| `docker-patterns` | 多阶段构建 + docker-compose |
| `security-review` | OWASP 检查 |

## 测试策略

```
单元测试          → Service 层业务逻辑
集成测试          → API 端点 + 数据库交互
契约测试（可选）   → OpenAPI schema 一致性
```

## 生成的产物

```
TaskFlow.Api/
├── Endpoints/          # Minimal API 端点定义
├── Services/           # 业务逻辑层
├── Repositories/       # 数据访问层
├── Models/             # 实体 + DTO
├── Validators/         # FluentValidation 验证器
├── Middleware/          # 异常处理 + 日志
├── Migrations/         # EF Core 迁移
├── Tests/              # 单元 + 集成测试
├── Dockerfile
├── docker-compose.yml
└── .opc/               # SuperOPC 项目状态
```
