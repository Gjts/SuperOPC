---
name: frontend-patterns
description: Use when building UI components, managing state, handling forms, or optimizing frontend performance. Covers React, Next.js, TailwindCSS, and modern frontend patterns.
---

## 前端开发模式

**使用方式：** 由实现 / 审查 agent 按技术栈上下文引用此工程模式手册。

## 何时激活

- 构建 React/Next.js 组件
- 管理客户端状态
- 处理表单验证
- 优化前端性能
- 实现响应式布局

## 组件设计

### 组件分层

```
components/
  ui/           # 原子组件（Button, Input, Card）
  features/     # 功能组件（UserCard, PaymentForm）
  layouts/      # 布局组件（Sidebar, Header）
```

### 组件模式

```tsx
// ✓ 纯展示组件 — 无状态，接收 props
interface UserCardProps {
  user: User;
  onSelect: (id: string) => void;
}

export function UserCard({ user, onSelect }: UserCardProps) {
  return (
    <div onClick={() => onSelect(user.id)}>
      <h3>{user.name}</h3>
      <p>{user.email}</p>
    </div>
  );
}

// ✓ 容器组件 — 管理状态，传递给展示组件
export function UserList() {
  const { data: users } = useQuery(['users'], fetchUsers);
  const handleSelect = (id: string) => router.push(`/users/${id}`);

  return users?.map(u => <UserCard key={u.id} user={u} onSelect={handleSelect} />);
}
```

## 状态管理

### 状态选择决策树

```
这个状态其他组件需要吗？
  ├── 否 → useState / useReducer
  └── 是 → 需要在服务端和客户端共享？
            ├── 是 → Server State (React Query / SWR)
            └── 否 → 多少组件共享？
                      ├── 2-3 个 → Context + useReducer
                      └── 多个 → Zustand / Jotai
```

### Server State（推荐 React Query）

```tsx
function useUser(id: string) {
  return useQuery({
    queryKey: ['user', id],
    queryFn: () => fetch(`/api/users/${id}`).then(r => r.json()),
    staleTime: 5 * 60 * 1000,  // 5 分钟内不重新请求
  });
}
```

## 表单处理

```tsx
// React Hook Form + Zod
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email('邮箱格式无效'),
  password: z.string().min(8, '至少8位'),
});

export function LoginForm() {
  const { register, handleSubmit, formState: { errors } } = useForm({
    resolver: zodResolver(schema),
  });

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input {...register('email')} />
      {errors.email && <span>{errors.email.message}</span>}
    </form>
  );
}
```

## 性能优化

| 问题 | 解决方案 |
|------|---------|
| 组件不必要重渲染 | `React.memo` + `useMemo` + `useCallback` |
| 大列表 | 虚拟化（`@tanstack/react-virtual`） |
| 图片加载慢 | `next/image` + lazy loading |
| 首屏加载大 | 动态导入 `next/dynamic` |
| 字体闪烁 | `next/font` + `font-display: swap` |

## TailwindCSS 规范

```tsx
// ✓ 使用语义化类名组合
<button className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-white
  hover:bg-primary/90 focus-visible:outline-2 focus-visible:outline-offset-2
  disabled:opacity-50 disabled:cursor-not-allowed">
  保存
</button>

// ✓ 响应式：mobile-first
<div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
```

## 一人公司前端清单

- [ ] 组件库（shadcn/ui 或 Radix）而非从零构建
- [ ] 表单验证（Zod schema 前后端共享）
- [ ] 错误边界（每个路由级别）
- [ ] 加载/空状态/错误状态（每个数据展示）
- [ ] 响应式设计（mobile-first）
- [ ] 可访问性基础（语义 HTML + aria 属性）

## 压力测试

### 高压场景
- 前端交互一复杂，就把状态和视图揉成一团。

### 常见偏差
- 组件职责不清，状态到处散落。

### 应用本手册后的纠正
- 按组件边界和状态流设计，保持可组合和可测。

