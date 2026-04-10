---
paths:
  - "**/*.ts"
  - "**/*.tsx"
  - "**/*.js"
  - "**/*.jsx"
---
# TypeScript/JavaScript Coding Style

> 扩展 [common/coding-style.md](../common/coding-style.md)，适用于 Next.js 14 + React + TailwindCSS 技术栈。

## 类型和接口

### 公共 API
- 导出函数添加参数和返回类型
- 让 TypeScript 推断局部变量类型
- 重复的内联对象形状提取为命名类型

```typescript
interface User {
  firstName: string
  lastName: string
}

export function formatUser(user: User): string {
  return `${user.firstName} ${user.lastName}`
}
```

### interface vs type
- `interface` 用于可能被扩展或实现的对象形状
- `type` 用于联合、交叉、元组、映射类型
- 字符串字面量联合优于 `enum`

### 避免 any
- 应用代码中避免 `any`
- 外部/不可信输入使用 `unknown`，然后安全收窄
- 类型依赖调用方时使用泛型

## React Props
- 使用命名 `interface` 定义组件 Props
- 显式类型化回调 Props
- 不使用 `React.FC`

```typescript
interface UserCardProps {
  user: User
  onSelect: (id: string) => void
}

function UserCard({ user, onSelect }: UserCardProps) {
  return <button onClick={() => onSelect(user.id)}>{user.email}</button>
}
```

## 不可变性

```typescript
// 错误：原地修改
function updateUser(user: User, name: string): User {
  user.name = name
  return user
}

// 正确：展开运算符
function updateUser(user: Readonly<User>, name: string): User {
  return { ...user, name }
}
```

## 错误处理

async/await + try-catch + 安全收窄 unknown：

```typescript
async function loadUser(userId: string): Promise<User> {
  try {
    return await riskyOperation(userId)
  } catch (error: unknown) {
    logger.error('Operation failed', error)
    throw new Error(error instanceof Error ? error.message : 'Unexpected error')
  }
}
```

## 输入验证（Zod）

```typescript
import { z } from 'zod'

const userSchema = z.object({
  email: z.string().email(),
  age: z.number().int().min(0).max(150)
})

type UserInput = z.infer<typeof userSchema>
```

## Next.js 14 规范

### App Router
- 使用 Server Components 作为默认
- 仅在需要交互时使用 `'use client'`
- 数据获取用 Server Actions 或 Route Handlers

### Server Actions
```typescript
'use server'

export async function createUser(formData: FormData) {
  const validated = userSchema.parse({
    email: formData.get('email'),
    name: formData.get('name')
  })
  // ...
}
```

## Console.log
- 生产代码中**禁止** `console.log`
- 使用正式的日志库
- hooks 系统会自动检测并警告
