---
name: dotnet-patterns
description: Use when building with .NET 8 Minimal API and EF Core. Covers endpoint mapping, dependency injection, EF Core patterns, middleware pipeline, and production-ready .NET patterns.
---

## .NET 8 Minimal API 模式

**使用方式：** 由实现 / 审查 agent 按技术栈上下文引用此工程模式手册。

## 何时激活

- 创建 .NET 8 API 端点
- 配置依赖注入
- 编写 EF Core 查询
- 设置中间件管道
- 实现认证/授权
- 优化性能

## Minimal API 端点

```csharp
// Program.cs
var builder = WebApplication.CreateBuilder(args);

// 注册服务
builder.Services.AddScoped<IUserRepository, UserRepository>();
builder.Services.AddScoped<IUserService, UserService>();
builder.Services.AddDbContext<AppDbContext>(o =>
    o.UseNpgsql(builder.Configuration.GetConnectionString("Default")));

var app = builder.Build();

// 端点分组
var users = app.MapGroup("/api/v1/users")
    .RequireAuthorization();

users.MapGet("/", async (IUserService svc, [AsParameters] UserQuery query) =>
    Results.Ok(await svc.GetAll(query)));

users.MapGet("/{id:guid}", async (Guid id, IUserService svc) =>
    await svc.GetById(id) is { } user
        ? Results.Ok(user)
        : Results.NotFound());

users.MapPost("/", async (CreateUserRequest req, IUserService svc) =>
{
    var user = await svc.Create(req);
    return Results.Created($"/api/v1/users/{user.Id}", user);
});
```

## EF Core 模式

### DbContext 配置

```csharp
public class AppDbContext : DbContext
{
    public AppDbContext(DbContextOptions<AppDbContext> options) : base(options) { }

    public DbSet<User> Users => Set<User>();
    public DbSet<Order> Orders => Set<Order>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.ApplyConfigurationsFromAssembly(typeof(AppDbContext).Assembly);
    }
}

// 实体配置（分离文件）
public class UserConfiguration : IEntityTypeConfiguration<User>
{
    public void Configure(EntityTypeBuilder<User> builder)
    {
        builder.HasKey(u => u.Id);
        builder.HasIndex(u => u.Email).IsUnique();
        builder.Property(u => u.Name).HasMaxLength(100).IsRequired();
    }
}
```

### 查询优化

```csharp
// ✓ 投影查询（只选需要的列）
var users = await db.Users
    .Where(u => u.IsActive)
    .Select(u => new UserDto(u.Id, u.Name, u.Email))
    .ToListAsync();

// ✓ 分页
var users = await db.Users
    .OrderBy(u => u.CreatedAt)
    .Skip((page - 1) * pageSize)
    .Take(pageSize)
    .ToListAsync();

// ✓ 避免 N+1
var users = await db.Users
    .Include(u => u.Orders)  // Eager loading
    .Where(u => u.IsActive)
    .ToListAsync();

// ✗ 避免在循环中查询
foreach (var user in users)
    user.Orders = await db.Orders.Where(o => o.UserId == user.Id).ToListAsync();
```

## 依赖注入

```csharp
// 生命周期选择
builder.Services.AddScoped<IUserRepository, UserRepository>();    // 每请求一个
builder.Services.AddSingleton<ICacheService, RedisCacheService>(); // 全局单例
builder.Services.AddTransient<IEmailService, EmailService>();      // 每次注入新建

// 选项模式
builder.Services.Configure<JwtOptions>(
    builder.Configuration.GetSection("Jwt"));

public class JwtOptions
{
    public string Secret { get; set; } = "";
    public int ExpiryMinutes { get; set; } = 60;
}
```

## 中间件管道

```csharp
// 顺序重要！
app.UseExceptionHandler("/error");  // 1. 全局错误处理
app.UseHsts();                       // 2. HSTS
app.UseHttpsRedirection();           // 3. HTTPS 重定向
app.UseCors("AllowFrontend");        // 4. CORS
app.UseAuthentication();             // 5. 认证
app.UseAuthorization();              // 6. 授权
app.UseRateLimiter();               // 7. 速率限制
```

## 输入验证

```csharp
// FluentValidation
public class CreateUserValidator : AbstractValidator<CreateUserRequest>
{
    public CreateUserValidator()
    {
        RuleFor(x => x.Email).NotEmpty().EmailAddress();
        RuleFor(x => x.Name).NotEmpty().MaximumLength(100);
        RuleFor(x => x.Password).NotEmpty().MinimumLength(8);
    }
}

// 注册验证过滤器
builder.Services.AddValidatorsFromAssemblyContaining<Program>();

// 端点使用
users.MapPost("/", async (CreateUserRequest req,
    IValidator<CreateUserRequest> validator, IUserService svc) =>
{
    var result = await validator.ValidateAsync(req);
    if (!result.IsValid) return Results.ValidationProblem(result.ToDictionary());
    return Results.Created("", await svc.Create(req));
});
```

## 一人公司 .NET 清单

- [ ] Minimal API（不用 Controller 模式）
- [ ] EF Core + PostgreSQL（Code-First 迁移）
- [ ] FluentValidation 输入验证
- [ ] JWT 认证 + 授权策略
- [ ] 全局错误处理中间件
- [ ] Serilog 结构化日志
- [ ] 健康检查端点
- [ ] OpenAPI/Swagger 文档

## 压力测试

### 高压场景
- 写 .NET 服务时把框架默认用法全堆在 Program.cs。

### 常见偏差
- 缺少清晰的依赖注入、验证和分层边界。

### 应用本手册后的纠正
- 采用 Minimal API + DI + 验证 + 分层约定。

