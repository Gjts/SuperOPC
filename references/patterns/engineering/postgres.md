---
name: postgres-patterns
description: Use when working with PostgreSQL 15. Covers indexing strategies, query optimization, RLS policies, partitioning, connection pooling, and Supabase-specific patterns.
---

## PostgreSQL 15 模式

**宣布：** "我正在使用 postgres-patterns 技能。"

## 何时激活

- 设计数据库 schema
- 优化慢查询
- 配置 RLS（行级安全）
- 添加索引
- 设置连接池
- 使用 Supabase 特定功能

## 索引策略

### 何时创建索引

```sql
-- WHERE 子句频繁过滤的列
CREATE INDEX idx_users_email ON users(email);

-- JOIN 条件列
CREATE INDEX idx_orders_user_id ON orders(user_id);

-- ORDER BY 排序列（与筛选组合）
CREATE INDEX idx_orders_user_created ON orders(user_id, created_at DESC);

-- 唯一约束（自动创建索引）
ALTER TABLE users ADD CONSTRAINT uq_users_email UNIQUE (email);
```

### 索引类型选择

| 类型 | 适用场景 | 示例 |
|------|---------|------|
| B-tree | 等值/范围查询（默认） | `WHERE email = ?` |
| GIN | 全文搜索、JSONB、数组 | `WHERE tags @> '{tag}'` |
| GiST | 地理位置、范围类型 | `WHERE location <@> point` |
| 部分索引 | 条件子集 | `WHERE is_active = true` |

```sql
-- 部分索引（只索引活跃用户）
CREATE INDEX idx_users_active_email ON users(email) WHERE is_active = true;

-- GIN 索引（JSONB 查询）
CREATE INDEX idx_users_metadata ON users USING GIN (metadata);
```

## 查询优化

### EXPLAIN ANALYZE

```sql
EXPLAIN (ANALYZE, BUFFERS, FORMAT TEXT)
SELECT * FROM orders WHERE user_id = '123' ORDER BY created_at DESC LIMIT 20;

-- 关注：
-- Seq Scan → 需要索引
-- Nested Loop → 可能 N+1
-- Sort → 需要排序索引
-- Rows Removed by Filter → 索引选择性差
```

### 常见优化

```sql
-- ✗ 慢：SELECT *
SELECT * FROM users WHERE department_id = 5;

-- ✓ 快：只选需要的列
SELECT id, name, email FROM users WHERE department_id = 5;

-- ✗ 慢：OFFSET 大数据集
SELECT * FROM orders ORDER BY created_at OFFSET 100000 LIMIT 20;

-- ✓ 快：Cursor 分页
SELECT * FROM orders
WHERE created_at < '2025-01-01'
ORDER BY created_at DESC LIMIT 20;

-- ✗ 慢：OR 多值
SELECT * FROM users WHERE status = 'active' OR status = 'pending';

-- ✓ 快：IN
SELECT * FROM users WHERE status IN ('active', 'pending');
```

## RLS（行级安全）— Supabase

```sql
-- 启用 RLS
ALTER TABLE orders ENABLE ROW LEVEL SECURITY;

-- 用户只能看自己的订单
CREATE POLICY "Users see own orders" ON orders
  FOR SELECT USING (auth.uid() = user_id);

-- 用户只能创建自己的订单
CREATE POLICY "Users create own orders" ON orders
  FOR INSERT WITH CHECK (auth.uid() = user_id);

-- 管理员可以看所有
CREATE POLICY "Admins see all orders" ON orders
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM user_roles WHERE user_id = auth.uid() AND role = 'admin')
  );
```

## 连接池

```
应用 → PgBouncer/Supavisor → PostgreSQL

配置建议（一人公司）：
- 连接池大小：10-20（不要超过 CPU 核数 × 2）
- 池模式：transaction（推荐）
- 空闲超时：300s
- 最大客户端连接：100
```

## 迁移最佳实践

```sql
-- ✓ 安全：添加可空列
ALTER TABLE users ADD COLUMN phone TEXT;

-- ✓ 安全：并发创建索引
CREATE INDEX CONCURRENTLY idx_users_phone ON users(phone);

-- ⚠️ 危险：删除列（先确认代码不再引用）
ALTER TABLE users DROP COLUMN old_field;

-- ⚠️ 危险：修改列类型（可能需要重写表）
ALTER TABLE users ALTER COLUMN age TYPE bigint;
```

## 一人公司 PostgreSQL 清单

- [ ] 主键用 UUID（`gen_random_uuid()`）
- [ ] `created_at` / `updated_at` 时间戳（每个表）
- [ ] RLS 策略（Supabase 必须）
- [ ] 外键约束 + ON DELETE 策略
- [ ] 频繁查询列有索引
- [ ] EXPLAIN ANALYZE 优化慢查询
- [ ] 连接池配置
- [ ] 定期 VACUUM ANALYZE

## 压力测试

### 高压场景
- 查询先写出来，慢了再说。

### 常见偏差
- 忽略索引、事务边界和连接池。

### 使用技能后的纠正
- 先按访问路径设计索引与事务，再落查询。

