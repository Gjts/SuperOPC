---
paths:
  - "**/*.cs"
---
# C# Testing

> 扩展 [common/testing.md](../common/testing.md)，适用于 .NET 8。

## 框架选择

| 场景 | 框架 | 包 |
|------|------|---|
| 单元测试 | xUnit | `xunit`, `xunit.runner.visualstudio` |
| Mock | NSubstitute | `NSubstitute` |
| 断言 | FluentAssertions | `FluentAssertions` |
| 集成测试 | WebApplicationFactory | `Microsoft.AspNetCore.Mvc.Testing` |
| 数据库测试 | Testcontainers | `Testcontainers.PostgreSql` |

## 单元测试结构

```csharp
public class UserServiceTests
{
    private readonly IUserRepository _repo = Substitute.For<IUserRepository>();
    private readonly UserService _sut;

    public UserServiceTests()
    {
        _sut = new UserService(_repo);
    }

    [Fact]
    public async Task CreateUser_WithValidInput_ReturnsUser()
    {
        // Arrange
        var request = new CreateUserRequest("test@example.com", "Test");

        // Act
        var result = await _sut.CreateAsync(request, CancellationToken.None);

        // Assert
        result.Email.Should().Be("test@example.com");
        await _repo.Received(1).SaveAsync(Arg.Any<User>(), Arg.Any<CancellationToken>());
    }

    [Fact]
    public async Task CreateUser_WithInvalidEmail_ThrowsValidationException()
    {
        var request = new CreateUserRequest("invalid", "Test");

        var act = () => _sut.CreateAsync(request, CancellationToken.None);

        await act.Should().ThrowAsync<ValidationException>();
    }
}
```

## Minimal API 集成测试

```csharp
public class UsersApiTests : IClassFixture<WebApplicationFactory<Program>>
{
    private readonly HttpClient _client;

    public UsersApiTests(WebApplicationFactory<Program> factory)
    {
        _client = factory.CreateClient();
    }

    [Fact]
    public async Task GetUser_ReturnsOk()
    {
        var response = await _client.GetAsync("/api/users/1");

        response.StatusCode.Should().Be(HttpStatusCode.OK);
    }

    [Fact]
    public async Task CreateUser_WithInvalidData_ReturnsBadRequest()
    {
        var content = JsonContent.Create(new { email = "bad" });

        var response = await _client.PostAsync("/api/users", content);

        response.StatusCode.Should().Be(HttpStatusCode.BadRequest);
    }
}
```

## 测试命名约定

```
{Method}_{Scenario}_{ExpectedResult}
```

示例：
- `CreateUser_WithValidInput_ReturnsUser`
- `CreateUser_WithDuplicateEmail_ThrowsConflict`
- `GetUser_WithInvalidId_ReturnsNotFound`
