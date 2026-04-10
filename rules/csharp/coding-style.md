---
paths:
  - "**/*.cs"
  - "**/*.csx"
---
# C# Coding Style

> 扩展 [common/coding-style.md](../common/coding-style.md)，适用于 .NET 8 Minimal API + EF Core 技术栈。

## 标准

- 遵循当前 .NET 约定，启用 nullable reference types
- 公共和 internal API 使用显式访问修饰符
- 文件与主类型对齐

## 类型和模型

- 不可变值模型优先使用 `record` 或 `record struct`
- 有身份和生命周期的实体使用 `class`
- 服务边界和抽象使用 `interface`
- 应用代码中避免 `dynamic`

```csharp
public sealed record UserDto(Guid Id, string Email);

public interface IUserRepository
{
    Task<UserDto?> FindByIdAsync(Guid id, CancellationToken ct);
}
```

## 不可变性

```csharp
public sealed record UserProfile(string Name, string Email);

public static UserProfile Rename(UserProfile profile, string name) =>
    profile with { Name = name };
```

## 异步和错误处理

- async/await 优于 .Result 或 .Wait()
- 公共异步 API 传递 CancellationToken
- 抛出具体异常，结构化日志记录

```csharp
public async Task<Order> LoadOrderAsync(
    Guid orderId, CancellationToken ct)
{
    try
    {
        return await repository.FindAsync(orderId, ct)
            ?? throw new InvalidOperationException($"Order {orderId} not found.");
    }
    catch (Exception ex)
    {
        logger.LogError(ex, "Failed to load order {OrderId}", orderId);
        throw;
    }
}
```

## Minimal API 模式

```csharp
var app = builder.Build();

app.MapGet("/api/users/{id:guid}", async (Guid id, IUserRepository repo, CancellationToken ct) =>
{
    var user = await repo.FindByIdAsync(id, ct);
    return user is not null ? Results.Ok(user) : Results.NotFound();
});

app.MapPost("/api/users", async (CreateUserRequest request, IUserService service, CancellationToken ct) =>
{
    var user = await service.CreateAsync(request, ct);
    return Results.Created($"/api/users/{user.Id}", user);
});
```

## EF Core 规范

- DbContext 使用 Scoped 生命周期
- 查询使用 AsNoTracking() 提升只读性能
- 批量操作使用 ExecuteUpdateAsync / ExecuteDeleteAsync
- 迁移文件**永不**手动修改

## 格式化

- 使用 `dotnet format` 统一格式
- 组织 using 指令，移除未使用的
- 表达式体成员仅在可读时使用
