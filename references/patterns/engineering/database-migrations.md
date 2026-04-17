---
name: database-migrations
description: Use when creating, modifying, or reviewing database migrations. Covers schema versioning, rollback safety, ORM drift detection, and zero-downtime migration patterns.
---

## 数据库迁移

**宣布：** "我正在使用 database-migrations 技能来管理数据库变更。"

## 何时激活

- 创建或修改数据库表/列/索引
- 添加或变更 ORM 模型
- 检查 schema drift（ORM 模型与实际数据库不一致）
- 执行生产环境数据迁移
- 计划零停机时间的 schema 变更

## 铁律

```
每次 schema 变更必须有对应的迁移文件。永远不要手动修改生产数据库。
```

## 迁移生命周期

### 1. 创建迁移

```bash
# EF Core (.NET)
dotnet ef migrations add AddUserEmailIndex

# Prisma (Node.js)
npx prisma migrate dev --name add_user_email_index

# Alembic (Python)
alembic revision --autogenerate -m "add_user_email_index"

# Supabase
supabase migration new add_user_email_index
```

### 2. 审查迁移（必须人工审查）

检查清单：
- [ ] SQL 语句是否正确？
- [ ] 是否有数据丢失风险？（DROP COLUMN, ALTER TYPE）
- [ ] 大表操作是否会锁表？
- [ ] 是否有回滚脚本？
- [ ] 索引是否用 `CONCURRENTLY` 创建？

### 3. 测试迁移

```bash
# 在测试环境运行
migrate up → 验证 → migrate down → 验证

# 确认幂等性
migrate up → migrate up → 无错误
```

## ORM Schema Drift 检测

```bash
# EF Core
dotnet ef migrations has-pending-changes

# Prisma
npx prisma migrate diff --from-schema-datasource --to-schema-datamodel

# Alembic
alembic check
```

**发现 drift 时：**
1. 不要手动修改数据库来匹配代码
2. 创建新迁移来弥合差距
3. 记录为什么会发生 drift
4. 如果工具链不可用，至少保留“schema 文件存在但迁移缺失”的建议性 finding，供 `/opc-health` 报告

## 零停机迁移模式

### 添加列（安全）
```sql
-- ✓ 安全：新列可为空
ALTER TABLE users ADD COLUMN phone TEXT;
```

### 删除列（两阶段）
```sql
-- 阶段 1：代码停止读写该列（部署代码）
-- 阶段 2：删除列（部署迁移）
ALTER TABLE users DROP COLUMN old_field;
```

### 重命名列（三阶段）
```sql
-- 阶段 1：添加新列 + 双写
ALTER TABLE users ADD COLUMN full_name TEXT;
UPDATE users SET full_name = name;
-- 阶段 2：代码切换到新列
-- 阶段 3：删除旧列
ALTER TABLE users DROP COLUMN name;
```

### 大表索引（并发创建）
```sql
-- ✓ 不锁表
CREATE INDEX CONCURRENTLY idx_users_email ON users(email);

-- ✗ 会锁表！
CREATE INDEX idx_users_email ON users(email);
```

## 数据迁移 vs Schema 迁移

| 类型 | 内容 | 回滚 |
|------|------|------|
| Schema | DDL（CREATE/ALTER/DROP） | 通常可逆 |
| Data | DML（INSERT/UPDATE/DELETE） | 需要备份 |

**数据迁移规则：**
- 始终先备份
- 分批处理（每批 1000-5000 行）
- 添加进度日志
- 设置超时保护

## 一人公司迁移清单

- [ ] 每次 schema 变更有迁移文件
- [ ] 迁移可回滚（up + down）
- [ ] CI 中运行 drift 检测
- [ ] 生产迁移前先在 staging 测试
- [ ] 大表操作用 CONCURRENTLY
- [ ] 数据迁移前备份

## 压力测试

### 高压场景
- 改了 schema，想先不写迁移直接上线。

### 常见偏差
- 把 ORM 模型修改当成数据库已同步。

### 使用技能后的纠正
- 每次 schema 变更都补迁移并做 drift 检查。

