---
paths:
  - "**/*.ts"
  - "**/*.tsx"
---
# TypeScript Security

> 扩展 [common/security.md](../common/security.md)

## Next.js 特定安全

### Server Actions
- 始终验证输入（Zod schema）
- 检查用户认证和授权
- 不信任客户端传来的任何数据

### API Routes
```typescript
// 每个 API Route 必须：
export async function POST(request: NextRequest) {
  // 1. 验证认证
  const session = await getServerSession()
  if (!session) return Response.json({ error: 'Unauthorized' }, { status: 401 })

  // 2. 验证输入
  const body = await request.json()
  const validated = schema.safeParse(body)
  if (!validated.success) return Response.json({ error: validated.error }, { status: 400 })

  // 3. 执行操作
  // 4. 返回结果
}
```

### 环境变量
- 客户端变量使用 `NEXT_PUBLIC_` 前缀
- 敏感变量**永不**使用 `NEXT_PUBLIC_`
- 启动时验证必需的环境变量

## Supabase 安全

- RLS（行级安全）**始终启用**
- 客户端只使用 `anon` key
- 服务端操作使用 `service_role` key
- 永不在客户端暴露 `service_role` key

## 依赖安全

```bash
npm audit                    # 检查已知漏洞
npm audit fix               # 自动修复
npm outdated                # 检查过期依赖
```

定期运行，CI 中强制执行。
