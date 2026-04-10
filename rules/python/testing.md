---
paths:
  - "**/test_*.py"
  - "**/*_test.py"
  - "**/conftest.py"
---
# Python Testing

> 扩展 [common/testing.md](../common/testing.md)

## 框架选择

| 场景 | 框架 | 安装 |
|------|------|------|
| 单元/集成测试 | pytest | `pip install pytest pytest-asyncio` |
| Mock | unittest.mock | 内置 |
| HTTP 测试 | httpx + pytest | `pip install httpx` |
| E2E | Playwright | `pip install playwright && playwright install` |
| 覆盖率 | coverage | `pip install pytest-cov` |

## 测试结构

```python
import pytest
from app.services.user import UserService

class TestUserService:
    """UserService 单元测试"""

    async def test_create_user_with_valid_input(self, user_service: UserService):
        # Arrange
        input_data = {"email": "test@example.com", "name": "Test"}

        # Act
        user = await user_service.create(input_data)

        # Assert
        assert user.email == "test@example.com"

    async def test_create_user_rejects_invalid_email(self, user_service: UserService):
        with pytest.raises(ValueError, match="Invalid email"):
            await user_service.create({"email": "bad", "name": "Test"})
```

## Fixtures

```python
import pytest
from unittest.mock import AsyncMock

@pytest.fixture
def mock_repo() -> AsyncMock:
    return AsyncMock()

@pytest.fixture
def user_service(mock_repo: AsyncMock) -> UserService:
    return UserService(repository=mock_repo)
```

## FastAPI 集成测试

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

class TestUsersAPI:
    async def test_get_users_returns_ok(self, client: AsyncClient):
        response = await client.get("/api/users")

        assert response.status_code == 200
        assert response.json()["success"] is True

    async def test_create_user_with_invalid_data_returns_422(self, client: AsyncClient):
        response = await client.post("/api/users", json={"email": "bad"})

        assert response.status_code == 422
```

## 测试命名约定

```
test_{method}_{scenario}_{expected_result}
```

示例：
- `test_create_user_with_valid_input_returns_user`
- `test_create_user_with_duplicate_email_raises_conflict`
- `test_get_user_with_invalid_id_returns_not_found`

## 配置（pyproject.toml）

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
addopts = "--cov=src --cov-report=term-missing --strict-markers"
markers = [
    "slow: marks tests as slow",
    "integration: marks integration tests",
]
```
