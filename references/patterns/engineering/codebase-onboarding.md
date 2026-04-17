---
name: codebase-onboarding
description: Use when joining a new project, analyzing an unfamiliar codebase, or generating a CLAUDE.md. Systematically maps architecture, entry points, conventions, and produces a structured onboarding guide.
---

## 代码库上手（棕地映射）

**宣布：** "我正在使用 codebase-onboarding 技能来分析此代码库。"

## 何时激活

- 首次在项目中使用 SuperOPC
- 加入新团队或仓库
- 用户说"帮我理解这个代码库"
- 用户要求生成 CLAUDE.md
- 用户说"带我了解这个仓库"

## 阶段 1: 侦察

并行运行以下检查（不读每个文件）：

```
1. 包管理检测
   → package.json, go.mod, Cargo.toml, pyproject.toml,
     *.csproj, build.gradle, Gemfile, pubspec.yaml

2. 框架指纹
   → next.config.*, nuxt.config.*, angular.json, vite.config.*,
     django settings, flask app, fastapi main, Program.cs

3. 入口点识别
   → main.*, index.*, app.*, server.*, cmd/, src/main/

4. 目录结构快照
   → 顶部 2 层目录树（忽略 node_modules, vendor, .git, dist）

5. 配置和工具检测
   → .eslintrc*, tsconfig.json, Dockerfile, docker-compose*,
     .github/workflows/, .env.example, CI 配置

6. 测试结构检测
   → tests/, __tests__/, *.spec.ts, *.test.js, pytest.ini,
     jest.config.*, vitest.config.*
```

## 阶段 2: 架构映射

```markdown
## 技术栈
- **语言**: TypeScript 5.x
- **框架**: Next.js 14 (App Router)
- **数据库**: PostgreSQL 15 (Supabase)
- **样式**: TailwindCSS 3.x
- **测试**: Vitest + Playwright
- **CI/CD**: GitHub Actions → Railway

## 架构模式
- App Router (Server Components 优先)
- Repository → Service → Route Handler
- Supabase RLS 行级安全

## 目录结构
src/
  app/           → 路由和页面
  components/    → UI 组件
  lib/           → 共享工具
  services/      → 业务逻辑
  types/         → TypeScript 类型
```

## 阶段 3: 关键路径

识别 5 条最重要的代码路径：

```
1. 用户注册流程: 
   signup page → auth API → Supabase Auth → welcome email

2. 核心功能路径:
   [识别产品的核心功能路径]

3. 支付流程:
   pricing page → Stripe checkout → webhook → subscription update
```

## 阶段 4: 约定检测

```markdown
## 编码约定
- 命名: camelCase 变量, PascalCase 组件, UPPER_SNAKE 常量
- 文件: kebab-case 文件名
- 导入: 绝对路径 (@/), 先外部后内部
- 测试: __tests__/ 目录, *.test.ts 命名
- Git: Conventional Commits (feat/fix/chore)
```

## 阶段 5: 生成 CLAUDE.md

```markdown
# CLAUDE.md

## 项目概述
[2-3 句话描述]

## 技术栈
[来自阶段 2]

## 开发命令
- `npm run dev` — 启动开发服务器
- `npm test` — 运行测试
- `npm run build` — 构建生产版本

## 代码结构
[来自阶段 2 目录结构]

## 编码约定
[来自阶段 4]

## 关键路径
[来自阶段 3]
```

## 输出物

1. **架构地图**（Markdown，写入 `.opc/PROJECT.md` 背景部分）
2. **CLAUDE.md**（项目根目录，如果不存在）
3. **关键路径文档**（帮助快速定位代码）
4. **技术债清单**（如果发现明显问题）

## 压力测试

### 高压场景
- 刚进新仓库，就立刻开始改代码。

### 常见偏差
- 没建立地图就做结论和重构。

### 使用技能后的纠正
- 先完成代码库地图和关键路径识别，再动实现。

