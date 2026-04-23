---
name: deployment-patterns
description: Use when planning deployment strategy, setting up CI/CD pipelines, or choosing between blue-green, canary, and rolling deployments. Covers zero-downtime patterns for Railway, Cloudflare, and general PaaS.
---

## 部署模式

**使用方式：** 由实现 / 审查 agent 按技术栈上下文引用此工程模式手册。

## 何时激活

- 设置 CI/CD 流水线
- 选择部署策略
- 实现零停机部署
- 配置回滚机制
- 规划蓝绿/金丝雀发布

## 部署策略对比

| 策略 | 复杂度 | 回滚速度 | 风险 | 适合 |
|------|--------|---------|------|------|
| **滚动** | 低 | 中 | 中 | 常规更新 |
| **蓝绿** | 中 | 即时 | 低 | 关键服务 |
| **金丝雀** | 高 | 快 | 最低 | 大用户群 |
| **重建** | 最低 | 慢 | 高 | 开发环境 |

## 滚动部署（Rolling）

```yaml
# Railway / Fly.io / Render 默认模式
# 逐步替换旧实例

优点：
- 零停机（新旧实例并存）
- 资源利用高效
- 大多数 PaaS 默认支持

注意：
- 同时运行新旧版本 → 需要向后兼容
- 数据库迁移必须先于代码部署
```

## 蓝绿部署（Blue-Green）

```
         ┌─── Blue (当前版本) ← 流量
用户 ──→ │
         └─── Green (新版本)   ← 预热中

切换后：
         ┌─── Blue (旧版本)   ← 备用
用户 ──→ │
         └─── Green (新版本)  ← 流量
```

```bash
# Cloudflare Workers 示例
wrangler publish --env production    # 部署到 green
# 验证 green 环境
# 切换 DNS/路由到 green
# 保留 blue 作为回滚目标
```

## 金丝雀部署（Canary）

```
用户 ──→ [负载均衡器]
           ├── 95% → 稳定版本
           └──  5% → 金丝雀版本

逐步增加：5% → 25% → 50% → 100%
每步监控错误率、延迟、业务指标
```

## CI/CD 流水线模板

```yaml
# GitHub Actions 示例
name: Deploy
on:
  push:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci
      - run: npm test
      - run: npm run lint

  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service app
```

## 回滚策略

```
发现问题 → 5分钟内决定
          ├── 轻微 → 热修复 forward
          └── 严重 → 立即回滚
                    ├── PaaS：一键回滚到上一版本
                    ├── Docker：切换到上一个镜像标签
                    └── 数据库：如果有迁移，执行 down
```

## 部署前检查清单

- [ ] 所有测试通过
- [ ] 数据库迁移已准备（且可回滚）
- [ ] 环境变量已配置
- [ ] 健康检查端点就绪
- [ ] 监控告警已设置
- [ ] 回滚计划已准备
- [ ] 变更已记录（CHANGELOG）

## 一人公司部署建议

- **用 PaaS**（Railway/Render/Fly.io），不要自建 K8s
- **main 分支自动部署**，staging 分支预览
- **数据库迁移先于代码部署**
- **健康检查 + 自动回滚**
- **部署后监控 15 分钟**再确认

## 压力测试

### 高压场景
- 上线前只确认“本地能跑”。

### 常见偏差
- 没有回滚路径和发布验证。

### 应用本手册后的纠正
- 选择合适部署策略并明确回滚与观测信号。

