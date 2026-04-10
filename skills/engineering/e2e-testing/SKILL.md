---
name: e2e-testing
description: Use when writing end-to-end tests with Playwright. Covers test structure, page objects, fixtures, visual regression, and CI integration for web applications.
---

## E2E 测试（Playwright）

**宣布：** "我正在使用 e2e-testing 技能来编写端到端测试。"

## 何时激活

- 编写新的 E2E 测试
- 设置 Playwright 测试基础设施
- 添加视觉回归测试
- 配置 CI 中的 E2E 测试
- 调试失败的 E2E 测试

## 项目设置

```bash
npm init playwright@latest
# 选择 TypeScript, tests 目录, GitHub Actions workflow
```

```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    { name: 'chromium', use: { ...devices['Desktop Chrome'] } },
    { name: 'mobile', use: { ...devices['iPhone 14'] } },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

## 测试结构

```typescript
import { test, expect } from '@playwright/test';

test.describe('用户登录', () => {
  test('有效凭证应成功登录', async ({ page }) => {
    // Arrange
    await page.goto('/login');

    // Act
    await page.fill('[data-testid="email"]', 'user@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');

    // Assert
    await expect(page).toHaveURL('/dashboard');
    await expect(page.locator('[data-testid="welcome"]')).toBeVisible();
  });

  test('无效凭证应显示错误', async ({ page }) => {
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'wrong@example.com');
    await page.fill('[data-testid="password"]', 'wrong');
    await page.click('[data-testid="login-button"]');

    await expect(page.locator('[data-testid="error"]')).toContainText('Invalid');
  });
});
```

## Page Object 模式

```typescript
// e2e/pages/login.page.ts
export class LoginPage {
  constructor(private page: Page) {}

  async goto() {
    await this.page.goto('/login');
  }

  async login(email: string, password: string) {
    await this.page.fill('[data-testid="email"]', email);
    await this.page.fill('[data-testid="password"]', password);
    await this.page.click('[data-testid="login-button"]');
  }

  async expectError(message: string) {
    await expect(this.page.locator('[data-testid="error"]'))
      .toContainText(message);
  }
}

// 使用
test('登录流程', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await loginPage.goto();
  await loginPage.login('user@example.com', 'password123');
  await expect(page).toHaveURL('/dashboard');
});
```

## Fixtures

```typescript
// e2e/fixtures.ts
import { test as base } from '@playwright/test';
import { LoginPage } from './pages/login.page';

type Fixtures = {
  loginPage: LoginPage;
  authenticatedPage: Page;
};

export const test = base.extend<Fixtures>({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
  authenticatedPage: async ({ page }, use) => {
    await page.goto('/login');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'password123');
    await page.click('[data-testid="login-button"]');
    await page.waitForURL('/dashboard');
    await use(page);
  },
});
```

## 视觉回归测试

```typescript
test('首页截图匹配', async ({ page }) => {
  await page.goto('/');
  await expect(page).toHaveScreenshot('homepage.png', {
    maxDiffPixelRatio: 0.01,
  });
});
```

## CI 配置

```yaml
# GitHub Actions
- name: Run E2E Tests
  uses: actions/setup-node@v4
  with:
    node-version: 20
- run: npx playwright install --with-deps
- run: npx playwright test
- uses: actions/upload-artifact@v4
  if: failure()
  with:
    name: playwright-report
    path: playwright-report/
```

## 一人公司 E2E 策略

- 关键用户路径优先（注册→登录→核心功能→支付）
- 不测试样式细节，测试功能行为
- CI 中只跑 chromium，本地跑多浏览器
- 失败时自动截图 + trace
- `data-testid` 属性定位，不依赖 CSS class
