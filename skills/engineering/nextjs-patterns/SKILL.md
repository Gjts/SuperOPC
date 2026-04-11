---
name: nextjs-patterns
description: Use when building with Next.js 14 App Router. Covers Server Components, Server Actions, route handlers, middleware, caching, and data fetching patterns specific to the App Router paradigm.
---

## Next.js 14 App Router 模式

**宣布：** "我正在使用 nextjs-patterns 技能。"

## 何时激活

- 创建新页面或路由
- 选择 Server Component vs Client Component
- 实现数据获取策略
- 使用 Server Actions
- 配置缓存和重验证
- 设置中间件（认证、国际化）

## Server vs Client Component

```
默认 = Server Component（无 'use client' 指令）

何时使用 Client Component？
├── 使用 useState / useEffect / useReducer
├── 使用浏览器 API（window, document, localStorage）
├── 事件处理器（onClick, onChange）
├── 使用 React Context
└── 使用依赖客户端的第三方库
```

### 混合模式（推荐）

```tsx
// app/users/page.tsx — Server Component（默认）
import { UserList } from './user-list';

export default async function UsersPage() {
  const users = await getUsers(); // 服务端获取数据
  return <UserList initialUsers={users} />; // 传递给客户端组件
}

// app/users/user-list.tsx — Client Component
'use client';
export function UserList({ initialUsers }: { initialUsers: User[] }) {
  const [search, setSearch] = useState('');
  // 客户端交互逻辑
}
```

## 数据获取

### Server Component 直接获取

```tsx
// ✓ 推荐：Server Component 中直接 async/await
async function UsersPage() {
  const users = await db.user.findMany(); // 直接访问数据库
  return <UserTable users={users} />;
}
```

### 缓存策略

```tsx
// 静态数据（构建时缓存）
fetch(url, { cache: 'force-cache' }); // 默认

// 动态数据（每次请求）
fetch(url, { cache: 'no-store' });

// 定时重验证
fetch(url, { next: { revalidate: 60 } }); // 60 秒

// 按需重验证
import { revalidatePath, revalidateTag } from 'next/cache';
revalidatePath('/users');
revalidateTag('users');
```

## Server Actions

```tsx
// app/users/actions.ts
'use server';

import { revalidatePath } from 'next/cache';
import { z } from 'zod';

const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
});

export async function createUser(formData: FormData) {
  // 1. 验证输入
  const parsed = CreateUserSchema.safeParse({
    email: formData.get('email'),
    name: formData.get('name'),
  });
  if (!parsed.success) {
    return { error: parsed.error.flatten().fieldErrors };
  }

  // 2. 检查认证
  const session = await getSession();
  if (!session) throw new Error('Unauthorized');

  // 3. 执行操作
  await db.user.create({ data: parsed.data });

  // 4. 重验证缓存
  revalidatePath('/users');
}
```

### 表单中使用

```tsx
// Client Component
'use client';
import { useActionState } from 'react';
import { createUser } from './actions';

export function CreateUserForm() {
  const [state, formAction, pending] = useActionState(createUser, null);

  return (
    <form action={formAction}>
      <input name="email" type="email" required />
      {state?.error?.email && <span>{state.error.email}</span>}
      <button type="submit" disabled={pending}>
        {pending ? '创建中...' : '创建用户'}
      </button>
    </form>
  );
}
```

## Route Handlers

```tsx
// app/api/users/route.ts
import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams;
  const page = Number(searchParams.get('page') ?? 1);

  const users = await db.user.findMany({
    skip: (page - 1) * 20,
    take: 20,
  });

  return NextResponse.json({ data: users });
}

export async function POST(request: NextRequest) {
  const body = await request.json();
  // 验证 + 创建
  return NextResponse.json({ data: user }, { status: 201 });
}
```

## Middleware

```tsx
// middleware.ts（项目根目录）
import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

export function middleware(request: NextRequest) {
  const token = request.cookies.get('session');

  // 未认证 → 重定向到登录
  if (!token && request.nextUrl.pathname.startsWith('/dashboard')) {
    return NextResponse.redirect(new URL('/login', request.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ['/dashboard/:path*', '/api/:path*'],
};
```

## 项目结构

```
app/
  (auth)/           # 路由组：认证相关页面
    login/page.tsx
    signup/page.tsx
  (dashboard)/      # 路由组：仪表盘
    layout.tsx       # 共享侧边栏布局
    page.tsx         # /dashboard
    users/page.tsx   # /dashboard/users
  api/              # Route Handlers
    users/route.ts
  layout.tsx        # 根布局
  page.tsx          # 首页
components/
  ui/               # 原子组件
  features/         # 功能组件
lib/
  db.ts             # 数据库客户端
  auth.ts           # 认证工具
```

## 一人公司 Next.js 清单

- [ ] Server Components 优先，Client 仅用于交互
- [ ] Server Actions 处理表单（替代 API 路由）
- [ ] Zod 验证所有输入（前后端共享 schema）
- [ ] 适当的缓存策略（静态 / 动态 / 定时重验证）
- [ ] Middleware 处理认证路由守卫
- [ ] `loading.tsx` + `error.tsx` 每个路由段
- [ ] `next/image` + `next/font` 性能优化

## 压力测试

### 高压场景
- 看到 Next.js 新能力就全部混用。

### 常见偏差
- Server/Client 组件边界混乱，数据流不清。

### 使用技能后的纠正
- 先定渲染边界，再选择 Server Components、Actions 和 Route Handlers。

