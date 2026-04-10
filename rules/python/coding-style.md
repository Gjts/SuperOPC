---
paths:
  - "**/*.py"
  - "**/*.pyi"
---
# Python Coding Style

> 扩展 [common/coding-style.md](../common/coding-style.md)，适用于 Python 3.11+ 技术栈。

## 类型标注

### 公共 API
- 导出函数/方法添加参数和返回类型标注
- 私有/局部变量可省略（让 mypy 推断）
- 使用 `from __future__ import annotations` 延迟求值

```python
from __future__ import annotations

def format_user(user: User) -> str:
    return f"{user.first_name} {user.last_name}"
```

### 类型工具
- `TypedDict` 用于结构化字典
- `Literal` 用于字符串字面量联合
- `Protocol` 用于结构性子类型（鸭子类型接口）
- 避免 `Any`，不可信输入使用 `object` 后收窄

```python
from typing import Literal, TypedDict

class UserDict(TypedDict):
    email: str
    role: Literal["admin", "user", "guest"]
```

## 数据模型

### Pydantic v2（推荐）
- 外部输入验证首选 Pydantic
- 内部数据传输使用 `dataclass` 或 `NamedTuple`

```python
from pydantic import BaseModel, EmailStr

class CreateUserRequest(BaseModel):
    email: EmailStr
    name: str
    age: int = Field(ge=0, le=150)
```

### dataclass
```python
from dataclasses import dataclass

@dataclass(frozen=True)
class UserProfile:
    name: str
    email: str
```

## 不可变性

```python
# 错误：原地修改
def update_user(user: dict, name: str) -> dict:
    user["name"] = name
    return user

# 正确：创建新副本
def update_user(user: dict, name: str) -> dict:
    return {**user, "name": name}
```

- 优先使用 `frozen=True` 的 dataclass
- 使用 `tuple` 替代 `list` 表示不可变序列
- 避免 `list`/`dict` 作为默认参数

## 错误处理

```python
import logging

logger = logging.getLogger(__name__)

async def load_user(user_id: str) -> User:
    try:
        return await risky_operation(user_id)
    except ValueError as e:
        logger.error("Validation failed for user %s: %s", user_id, e)
        raise
    except Exception as e:
        logger.exception("Unexpected error loading user %s", user_id)
        raise RuntimeError(f"Failed to load user: {e}") from e
```

## 输入验证（Pydantic）

```python
from pydantic import BaseModel, EmailStr, Field

class UserInput(BaseModel):
    email: EmailStr
    age: int = Field(ge=0, le=150)
    name: str = Field(min_length=1, max_length=100)

# 快速失败
try:
    user = UserInput(**raw_data)
except ValidationError as e:
    return {"error": e.errors()}
```

## 项目结构

```
src/
  app/
    __init__.py
    main.py          # 入口
    config.py         # 配置
    models/           # 数据模型
    services/         # 业务逻辑
    api/              # 路由/端点
    repositories/     # 数据访问
tests/
  conftest.py
  test_*.py
```

## 格式化

- 使用 `ruff format`（替代 black）统一格式
- 使用 `ruff check` 替代 flake8 + isort
- 行宽 88（ruff 默认）
- 字符串统一使用双引号

## Console.log 等价物
- 生产代码中**禁止** `print()`
- 使用 `logging` 模块
- hooks 系统会自动检测并警告
