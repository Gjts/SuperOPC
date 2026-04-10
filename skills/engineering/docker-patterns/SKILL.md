---
name: docker-patterns
description: Use when containerizing applications, writing Dockerfiles, or setting up docker-compose. Covers multi-stage builds, security hardening, and production-ready patterns.
---

## Docker 容器化模式

**宣布：** "我正在使用 docker-patterns 技能来容器化应用。"

## 何时激活

- 创建或优化 Dockerfile
- 设置 docker-compose 开发环境
- 缩小镜像大小
- 安全加固容器
- 配置多阶段构建

## 多阶段构建（推荐）

### Node.js / Next.js

```dockerfile
# 阶段 1：依赖安装
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci --only=production

# 阶段 2：构建
FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

# 阶段 3：生产运行
FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production

RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 appuser

COPY --from=builder --chown=appuser:appgroup /app/.next/standalone ./
COPY --from=builder --chown=appuser:appgroup /app/.next/static ./.next/static
COPY --from=builder --chown=appuser:appgroup /app/public ./public

USER appuser
EXPOSE 3000
CMD ["node", "server.js"]
```

### .NET 8

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:8.0 AS build
WORKDIR /src
COPY *.csproj .
RUN dotnet restore
COPY . .
RUN dotnet publish -c Release -o /app

FROM mcr.microsoft.com/dotnet/aspnet:8.0 AS runtime
WORKDIR /app
COPY --from=build /app .
RUN adduser --disabled-password --gecos "" appuser
USER appuser
EXPOSE 8080
ENTRYPOINT ["dotnet", "MyApp.dll"]
```

### Python (FastAPI)

```dockerfile
FROM python:3.11-slim AS builder
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /install /usr/local
COPY . .
RUN useradd -r appuser
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## docker-compose 开发环境

```yaml
services:
  app:
    build: .
    ports: ["3000:3000"]
    volumes:
      - .:/app
      - /app/node_modules   # 匿名卷保护 node_modules
    env_file: .env.local
    depends_on:
      db: { condition: service_healthy }

  db:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: myapp
      POSTGRES_USER: dev
      POSTGRES_PASSWORD: devpass
    ports: ["5432:5432"]
    volumes: [pgdata:/var/lib/postgresql/data]
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dev"]
      interval: 5s
      timeout: 3s
      retries: 5

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

volumes:
  pgdata:
```

## 安全加固

1. **非 root 用户运行**
2. **使用 alpine/slim 基础镜像**
3. **.dockerignore** 排除敏感文件
4. **固定版本标签**（不用 `latest`）
5. **只复制必要文件**
6. **扫描漏洞**：`docker scout cves`

```dockerignore
.git
.env*
node_modules
*.md
tests/
.opc/
```

## 镜像大小优化

| 技巧 | 效果 |
|------|------|
| 多阶段构建 | 减少 50-80% |
| alpine 基础镜像 | 减少 60-70% |
| .dockerignore | 减少构建上下文 |
| npm ci --only=production | 排除 devDependencies |
| 合并 RUN 指令 | 减少层数 |

## 一人公司 Docker 清单

- [ ] 多阶段构建（dev 依赖不进生产镜像）
- [ ] 非 root 用户运行
- [ ] 健康检查配置
- [ ] .dockerignore 排除敏感文件
- [ ] 固定版本标签
- [ ] 定期漏洞扫描
