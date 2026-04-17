---
name: backend-patterns
description: Use when designing backend architecture, implementing repository/service/controller layers, optimizing database queries, or adding caching and background jobs.
---

## 后端开发模式

**宣布：** "我正在使用 backend-patterns 技能。"

## 何时激活

- 设计 REST/GraphQL API 端点
- 实现 Repository/Service/Controller 分层
- 优化数据库查询（N+1、索引、连接池）
- 添加缓存（Redis、内存、HTTP 缓存头）
- 设置后台任务/异步处理
- 构建中间件（认证、日志、速率限制）

## 分层架构

```
Controller/Route   ← 接收请求、验证输入、返回响应
    │
Service            ← 业务逻辑、编排多个 Repository
    │
Repository         ← 数据访问、封装查询
    │
Database           ← PostgreSQL / Redis / 外部 API
```

### Repository 模式

```typescript
// 抽象数据访问
interface UserRepository {
  findById(id: string): Promise<User | null>;
  findAll(filters?: UserFilters): Promise<User[]>;
  create(data: CreateUserDto): Promise<User>;
  update(id: string, data: UpdateUserDto): Promise<User>;
}

// Supabase 实现
class SupabaseUserRepository implements UserRepository {
  async findById(id: string): Promise<User | null> {
    const { data, error } = await supabase
      .from('users')
      .select('*')
      .eq('id', id)
      .single();
    if (error) throw new DatabaseError(error.message);
    return data;
  }
}
```

### Service 层

```typescript
class UserService {
  constructor(
    private userRepo: UserRepository,
    private emailService: EmailService,
  ) {}

  async createUser(input: CreateUserInput): Promise<User> {
    // 业务规则
    const existing = await this.userRepo.findByEmail(input.email);
    if (existing) throw new ConflictError('Email already registered');

    // 创建用户
    const user = await this.userRepo.create(input);

    // 副作用
    await this.emailService.sendWelcome(user.email);

    return user;
  }
}
```

## N+1 查询问题

```typescript
// ✗ N+1 问题
const users = await userRepo.findAll();
for (const user of users) {
  user.orders = await orderRepo.findByUserId(user.id); // N 次查询！
}

// ✓ JOIN 或 IN 查询
const users = await supabase
  .from('users')
  .select('*, orders(*)')  // 一次查询
  .limit(20);

// ✓ DataLoader 模式（GraphQL）
const loader = new DataLoader(async (userIds) => {
  const orders = await orderRepo.findByUserIds(userIds);
  return userIds.map(id => orders.filter(o => o.userId === id));
});
```

## 缓存策略

| 策略 | TTL | 适用场景 |
|------|-----|---------|
| **Cache-Aside** | 5-15 分钟 | 读多写少的数据 |
| **Write-Through** | - | 一致性要求高 |
| **TTL + Stale** | 1 小时 | 不常变化的配置 |

```typescript
async function getUser(id: string): Promise<User> {
  // 1. 查缓存
  const cached = await redis.get(`user:${id}`);
  if (cached) return JSON.parse(cached);

  // 2. 查数据库
  const user = await userRepo.findById(id);

  // 3. 写缓存
  await redis.setex(`user:${id}`, 300, JSON.stringify(user));

  return user;
}
```

## 错误处理

```typescript
// 自定义错误层级
class AppError extends Error {
  constructor(
    message: string,
    public code: string,
    public statusCode: number,
  ) { super(message); }
}

class NotFoundError extends AppError {
  constructor(resource: string) {
    super(`${resource} not found`, 'NOT_FOUND', 404);
  }
}

class ConflictError extends AppError {
  constructor(message: string) {
    super(message, 'CONFLICT', 409);
  }
}

// 全局错误处理中间件
function errorHandler(err: Error, req: Request, res: Response) {
  if (err instanceof AppError) {
    return res.status(err.statusCode).json({
      error: { code: err.code, message: err.message }
    });
  }
  // 未预期错误
  logger.error(err);
  return res.status(500).json({
    error: { code: 'INTERNAL_ERROR', message: 'Something went wrong' }
  });
}
```

## 一人公司后端清单

- [ ] 分层架构（Controller → Service → Repository）
- [ ] 统一错误处理（自定义错误类 + 全局处理）
- [ ] 输入验证（Zod / FluentValidation / Pydantic）
- [ ] 请求日志 + traceId
- [ ] 健康检查端点（`/health`）
- [ ] 数据库连接池配置
- [ ] 速率限制（至少全局级别）

## 压力测试

### 高压场景
- 后端需求增加时，想把所有逻辑塞进 controller。

### 常见偏差
- 把路由、业务、存储逻辑混在一起。

### 使用技能后的纠正
- 按分层职责拆分 controller/service/repository。

