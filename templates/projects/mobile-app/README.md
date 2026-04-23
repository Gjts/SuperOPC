# Mobile App 模板

> Kotlin + Jetpack Compose — Android 原生应用模板

## 技术栈

| 层 | 技术 | 说明 |
|---|------|------|
| UI | Jetpack Compose + Material 3 | 声明式 UI |
| 架构 | MVVM + Clean Architecture | ViewModel + UseCase + Repository |
| 网络 | Retrofit + OkHttp | REST API 客户端 |
| 本地存储 | Room + DataStore | SQLite ORM + KV 存储 |
| DI | Hilt | 编译时依赖注入 |
| 导航 | Navigation Compose | 类型安全导航 |

## 适用场景

- Android 原生应用
- B2C 移动端产品
- 需要离线支持的工具类应用
- 社交/内容类应用

## 使用方式

```bash
# 1. 初始化项目
/opc-start

# 2. 选择此模板

# 3. 使用 Android Studio 创建项目
# File → New → New Project → Empty Compose Activity
# 最低 SDK: API 26 (Android 8.0)
```

## 预配置内容

```
.opc/
  PROJECT.md          # 移动应用项目定义
  REQUIREMENTS.md     # 典型移动端需求（登录/首页/设置/推送）
  ROADMAP.md          # 5 阶段路线图
  STATE.md            # 初始状态
  config.json         # 移动开发工作流配置
```

## 推荐入口与参考组合

| 阶段 | 入口 / 参考 |
|------|------|
| 设计 | `/opc-business`（product-lens / validate-idea 子活动） |
| 开发 | `/opc-plan` / `/opc-build` + `kotlin-compose.md` + `api-design.md` + `backend-patterns.md` |
| 测试 | `Skill("tdd")` + `references/patterns/engineering/e2e-testing.md` |
| 发布 | `references/patterns/engineering/deployment-patterns.md` |
| 增长 | `/opc-business`（first-customers / content-engine 子活动） |

## 适配的规则

- `rules/kotlin/` — Kotlin / Android 编码规范
- `rules/common/testing.md` — 测试优先
- `rules/common/security.md` — 移动端安全基线

## 关键架构决策

1. **Compose 优先** — 不使用 XML 布局
2. **单 Activity** — Navigation Compose 管理所有屏幕
3. **离线优先** — Room 本地缓存 + 网络同步
4. **State Hoisting** — UI 状态提升到 ViewModel
