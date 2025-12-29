# PostgreSQL 数据迁移指南

## 概述

本指南用于将芯片报价系统的 SQLite 数据库迁移到 PostgreSQL 生产环境。

## 迁移文件说明

### 生成的文件

1. **complete_migration.sql** (320KB)
   - 包含所有24个表的完整数据
   - 共 743 行数据
   - 按依赖关系顺序排列
   - 包含序列重置语句

2. **complete_migration.py**
   - Python 迁移脚本
   - 用于生成 SQL 文件

### 数据统计

| 表名 | 行数 | 说明 |
|------|------|------|
| users | 7 | 用户表 |
| machines | 8 | 设备表 |
| quotes | 87 | 报价单主表 |
| quote_items | 195 | 报价单明细 |
| card_configs | 65 | 卡片配置 |
| approval_instance | 63 | 审批实例 |
| approval_records | 106 | 审批记录 |
| user_sessions | 90 | 用户会话 |
| 其他表 | 122 | 其他业务数据 |
| **总计** | **743** | - |

## 服务器端迁移步骤

### 前提条件

1. **确保服务器已安装 PostgreSQL**
   ```bash
   psql --version
   ```

2. **确保已创建数据库**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE chip_quotation;
   CREATE USER chip_user WITH PASSWORD '你的密码';
   GRANT ALL PRIVILEGES ON DATABASE chip_quotation TO chip_user;
   \q
   ```

3. **确保服务器上已运行 SQLAlchemy 模型迁移创建表结构**
   ```bash
   cd /path/to/backend
   source venv/bin/activate

   # 如果使用 Alembic
   alembic upgrade head

   # 或者直接创建表（如果项目使用 create_all）
   python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
   ```

### 步骤 1: 传输文件到服务器

使用 scp 或其他方式传输 SQL 文件到服务器：

```bash
# 在本地执行
scp complete_migration.sql 用户名@服务器地址:/tmp/
```

### 步骤 2: 在服务器上备份现有数据（如果有）

```bash
# 在服务器上执行
sudo -u postgres pg_dump chip_quotation > /tmp/chip_quotation_backup_$(date +%Y%m%d_%H%M%S).sql
```

### 步骤 3: 执行迁移

```bash
# 在服务器上执行
sudo -u postgres psql chip_quotation -f /tmp/complete_migration.sql
```

如果使用自定义用户：

```bash
psql -U chip_user -d chip_quotation -f /tmp/complete_migration.sql
```

### 步骤 4: 验证数据

```bash
# 验证关键表的数据量
psql -U chip_user -d chip_quotation << EOF
SELECT 'users' as table_name, COUNT(*) as count FROM users
UNION ALL
SELECT 'machines', COUNT(*) FROM machines
UNION ALL
SELECT 'quotes', COUNT(*) FROM quotes
UNION ALL
SELECT 'quote_items', COUNT(*) FROM quote_items
UNION ALL
SELECT 'approval_instance', COUNT(*) FROM approval_instance
UNION ALL
SELECT 'card_configs', COUNT(*) FROM card_configs
ORDER BY table_name;
EOF
```

预期结果：
```
 table_name        | count
-------------------+-------
 approval_instance |    63
 card_configs      |    65
 machines          |     8
 quote_items       |   195
 quotes            |    87
 users             |     7
```

### 步骤 5: 验证外键关系

```bash
# 检查外键约束是否正常
psql -U chip_user -d chip_quotation -c "SELECT
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name
FROM information_schema.table_constraints AS tc
JOIN information_schema.key_column_usage AS kcu
    ON tc.constraint_name = kcu.constraint_name
JOIN information_schema.constraint_column_usage AS ccu
    ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY'
ORDER BY tc.table_name;"
```

### 步骤 6: 验证序列

```bash
# 检查序列是否正确设置
psql -U chip_user -d chip_quotation << EOF
SELECT
    schemaname,
    tablename,
    last_value
FROM pg_sequences
WHERE schemaname = 'public'
ORDER BY tablename;
EOF
```

### 步骤 7: 测试应用连接

```bash
# 更新 .env.prod 中的数据库连接字符串
DATABASE_URL=postgresql://chip_user:密码@localhost:5432/chip_quotation
```

启动后端服务并测试：

```bash
cd /path/to/backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

测试API：
```bash
curl http://localhost:8000/api/v1/quotes/
```

## 故障排除

### 问题 1: 权限错误

```
ERROR: permission denied for table xxx
```

**解决方案：**
```bash
# 授予所有表的权限
sudo -u postgres psql chip_quotation
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO chip_user;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO chip_user;
\q
```

### 问题 2: 表不存在

```
ERROR: relation "xxx" does not exist
```

**解决方案：**
确保先运行了 SQLAlchemy 模型创建表结构：
```bash
cd /path/to/backend
source venv/bin/activate
alembic upgrade head
```

### 问题 3: 数据类型不匹配

```
ERROR: invalid input syntax for type xxx
```

**解决方案：**
重新运行迁移脚本生成 SQL 文件，或手动调整 SQL 中的数据类型。

### 问题 4: 唯一约束冲突

```
ERROR: duplicate key value violates unique constraint
```

**解决方案：**
清空目标表后重新导入：
```bash
psql -U chip_user -d chip_quotation -c "TRUNCATE TABLE 表名 CASCADE;"
```

## 回滚方案

如果迁移失败，可以回滚到备份：

```bash
# 删除数据库
sudo -u postgres psql -c "DROP DATABASE chip_quotation;"

# 重新创建数据库
sudo -u postgres psql -c "CREATE DATABASE chip_quotation;"

# 恢复备份
sudo -u postgres psql chip_quotation < /tmp/chip_quotation_backup_时间戳.sql
```

## 性能优化建议

### 1. 创建索引（如果需要）

```sql
-- 为常用查询字段创建索引
CREATE INDEX idx_quotes_created_at ON quotes(created_at);
CREATE INDEX idx_quotes_status ON quotes(status);
CREATE INDEX idx_quote_items_quote_id ON quote_items(quote_id);
CREATE INDEX idx_approval_instance_quote_id ON approval_instance(quote_id);
```

### 2. 分析表统计信息

```sql
ANALYZE users;
ANALYZE machines;
ANALYZE quotes;
ANALYZE quote_items;
ANALYZE approval_instance;
```

### 3. 启用查询日志（仅用于调试）

在 postgresql.conf 中：
```
log_statement = 'all'
log_min_duration_statement = 1000  # 记录慢查询（1秒以上）
```

## 后续维护

### 定期备份

```bash
# 创建每日备份脚本
cat > /usr/local/bin/backup_chip_quotation.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/var/backups/postgresql"
mkdir -p $BACKUP_DIR
pg_dump -U chip_user chip_quotation | gzip > $BACKUP_DIR/chip_quotation_$(date +%Y%m%d_%H%M%S).sql.gz
# 保留最近7天的备份
find $BACKUP_DIR -name "chip_quotation_*.sql.gz" -mtime +7 -delete
EOF

chmod +x /usr/local/bin/backup_chip_quotation.sh

# 添加到 crontab (每天凌晨2点执行)
crontab -e
# 添加：0 2 * * * /usr/local/bin/backup_chip_quotation.sh
```

### 监控数据库性能

```bash
# 查看活动连接
psql -U chip_user -d chip_quotation -c "SELECT * FROM pg_stat_activity WHERE datname = 'chip_quotation';"

# 查看表大小
psql -U chip_user -d chip_quotation -c "SELECT
    schemaname,
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;"
```

## 联系支持

如遇到问题，请检查：
1. PostgreSQL 日志：`/var/log/postgresql/postgresql-版本-main.log`
2. 应用日志：`backend/backend.log`
3. 确保 PostgreSQL 版本与 SQLAlchemy 兼容

---

**生成时间：** 2025-10-24
**版本：** 1.0
**维护者：** 芯片报价系统开发团队
