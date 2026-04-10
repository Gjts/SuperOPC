---
paths:
  - "**/*.cs"
---
# C# Security

> 扩展 [common/security.md](../common/security.md)，适用于 .NET 8 + Supabase 认证。

## 认证和授权

```csharp
// Minimal API 认证
app.MapGet("/api/protected", [Authorize] async (ClaimsPrincipal user) =>
{
    var userId = user.FindFirst(ClaimTypes.NameIdentifier)?.Value;
    // ...
});

// 基于策略的授权
builder.Services.AddAuthorizationBuilder()
    .AddPolicy("AdminOnly", policy => policy.RequireRole("admin"));
```

## 输入验证

```csharp
// FluentValidation
public class CreateUserValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Password).MinimumLength(8);
    }
}

// Minimal API 集成
app.MapPost("/api/users", async (
    CreateUserRequest request,
    IValidator<CreateUserRequest> validator,
    CancellationToken ct) =>
{
    var result = await validator.ValidateAsync(request, ct);
    if (!result.IsValid) return Results.ValidationProblem(result.ToDictionary());
    // ...
});
```

## SQL 注入防护

- **始终**使用 EF Core 参数化查询
- **永不**拼接 SQL 字符串
- 原始 SQL 使用 `FromSqlInterpolated`

```csharp
// 正确
var users = await db.Users
    .Where(u => u.Email == email)
    .ToListAsync(ct);

// 正确（原始 SQL）
var users = await db.Users
    .FromSqlInterpolated($"SELECT * FROM users WHERE email = {email}")
    .ToListAsync(ct);

// 错误！SQL 注入风险
var users = await db.Users
    .FromSqlRaw($"SELECT * FROM users WHERE email = '{email}'")
    .ToListAsync(ct);
```

## 密钥管理

```csharp
// 使用 IConfiguration，不硬编码
var apiKey = builder.Configuration["Stripe:SecretKey"]
    ?? throw new InvalidOperationException("Stripe:SecretKey not configured");

// 生产环境使用 User Secrets 或环境变量
// dotnet user-secrets set "Stripe:SecretKey" "sk_live_..."
```

## CORS 配置

```csharp
builder.Services.AddCors(options =>
{
    options.AddDefaultPolicy(policy =>
    {
        policy.WithOrigins("https://yourdomain.com")
              .AllowAnyHeader()
              .AllowAnyMethod()
              .AllowCredentials();
    });
});
```
