---
paths:
  - "**/*.test.ts"
  - "**/*.test.tsx"
  - "**/*.spec.ts"
  - "**/*.spec.tsx"
---
# TypeScript Testing

> 扩展 [common/testing.md](../common/testing.md)

## 框架选择

| 场景 | 框架 | 安装 |
|------|------|------|
| Next.js 项目 | Vitest | `npm install -D vitest @testing-library/react` |
| Node.js 项目 | Jest | `npm install -D jest @types/jest ts-jest` |
| API 测试 | supertest | `npm install -D supertest @types/supertest` |
| E2E | Playwright | `npm install -D @playwright/test` |

## 测试结构

```typescript
import { describe, it, expect } from 'vitest'

describe('UserService', () => {
  describe('createUser', () => {
    it('should create user with valid input', async () => {
      // Arrange
      const input = { email: 'test@example.com', name: 'Test' }

      // Act
      const user = await createUser(input)

      // Assert
      expect(user.email).toBe('test@example.com')
    })

    it('should reject invalid email', async () => {
      await expect(createUser({ email: 'bad', name: 'Test' }))
        .rejects.toThrow('Invalid email')
    })
  })
})
```

## React 组件测试

```typescript
import { render, screen, fireEvent } from '@testing-library/react'

it('should call onSubmit with form data', async () => {
  const onSubmit = vi.fn()
  render(<LoginForm onSubmit={onSubmit} />)

  await fireEvent.change(screen.getByLabelText('Email'), {
    target: { value: 'test@example.com' }
  })
  await fireEvent.click(screen.getByRole('button', { name: 'Submit' }))

  expect(onSubmit).toHaveBeenCalledWith({ email: 'test@example.com' })
})
```

## API Route 测试

```typescript
import { GET, POST } from '@/app/api/users/route'
import { NextRequest } from 'next/server'

it('should return users list', async () => {
  const response = await GET()
  const data = await response.json()

  expect(response.status).toBe(200)
  expect(data.success).toBe(true)
  expect(Array.isArray(data.data)).toBe(true)
})
```
