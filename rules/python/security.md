---
paths:
  - "**/*.py"
---
# Python Security

> 扩展 [common/security.md](../common/security.md)

## 输入验证

```python
from pydantic import BaseModel, EmailStr, Field

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str = Field(min_length=1, max_length=100)
    password: str = Field(min_length=8, max_length=128)

# 每个端点必须：
async def create_user(request: Request):
    # 1. 验证输入（Pydantic 自动完成）
    data = CreateUserRequest(**await request.json())
    # 2. 检查认证
    # 3. 检查授权
    # 4. 执行操作
```

## SQL 注入防护

- **始终**使用 ORM 参数化查询（SQLAlchemy / asyncpg）
- **永不**拼接 SQL 字符串

```python
# 正确 — SQLAlchemy ORM
users = await session.execute(
    select(User).where(User.email == email)
)

# 正确 — 参数化原始 SQL
result = await session.execute(
    text("SELECT * FROM users WHERE email = :email"),
    {"email": email}
)

# 错误！SQL 注入风险
result = await session.execute(
    text(f"SELECT * FROM users WHERE email = '{email}'")
)
```

## 认证

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer

security = HTTPBearer()

async def get_current_user(
    credentials = Depends(security),
    db = Depends(get_db)
) -> User:
    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )
    user = await db.get(User, payload["sub"])
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user
```

## 密钥管理

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    DATABASE_URL: str
    STRIPE_SECRET_KEY: str

    model_config = {"env_file": ".env"}

# 启动时验证
settings = Settings()  # 缺失必需变量会立即报错
```

- **永不**硬编码密钥
- 使用 `pydantic-settings` 从环境变量加载
- `.env` 文件在 `.gitignore` 中

## 路径遍历防护

```python
from pathlib import Path

UPLOAD_DIR = Path("/app/uploads").resolve()

def safe_path(filename: str) -> Path:
    """防止路径遍历攻击"""
    target = (UPLOAD_DIR / filename).resolve()
    if not target.is_relative_to(UPLOAD_DIR):
        raise ValueError("Path traversal detected")
    return target
```

## 依赖安全

```bash
pip-audit                    # 检查已知漏洞
safety check                 # 替代方案
pip list --outdated          # 检查过期依赖
```

定期运行，CI 中强制执行。

## 一人公司安全清单

- [ ] Pydantic 验证所有外部输入
- [ ] JWT + HTTPOnly Cookie 认证
- [ ] ORM 参数化查询（无原始 SQL 拼接）
- [ ] 环境变量管理密钥（pydantic-settings）
- [ ] CORS 限制允许的源
- [ ] 速率限制（slowapi / fastapi-limiter）
- [ ] 依赖审计（pip-audit）
