# PostgreSQL 数据迁移 - 快速操作步骤

## 📋 准备工作检查清单

- [x] 已备份本地 SQLite 数据库
- [x] 已生成 complete_migration.sql (320KB, 743行数据)
- [x] 已创建详细迁移指南文档
- [ ] 服务器已安装并配置 PostgreSQL
- [ ] 服务器已创建数据库和用户
- [ ] 服务器已运行表结构迁移（Alembic）

## 🚀 三步快速迁移

### 步骤 1: 传输文件

```bash
# 在本地执行（backend 目录下）
scp complete_migration.sql 服务器用户@服务器IP:/tmp/
```

### 步骤 2: 执行迁移

```bash
# 在服务器上执行
sudo -u postgres psql 数据库名 -f /tmp/complete_migration.sql
```

### 步骤 3: 验证数据

```bash
# 在服务器上执行
psql -U 用户名 -d 数据库名 << 'EOF'
SELECT 'users' as table_name, COUNT(*) FROM users
UNION ALL SELECT 'quotes', COUNT(*) FROM quotes
UNION ALL SELECT 'quote_items', COUNT(*) FROM quote_items;
EOF
```

**预期结果：**
- users: 7
- quotes: 87
- quote_items: 195

## 📊 数据概览

| 分类 | 表数量 | 数据行数 |
|------|--------|----------|
| 基础表（用户、设备等） | 6 | 28 |
| 设备相关表 | 3 | 73 |
| 报价相关表 | 7 | 300 |
| 审批相关表 | 4 | 260 |
| 日志和会话表 | 2 | 90 |
| **总计** | **22** | **743** |

## ⚠️ 重要提醒

1. **确保服务器已运行表结构迁移**（Alembic upgrade head）
2. **备份服务器现有数据**（如果有）
3. **使用正确的数据库名和用户名**
4. **迁移后验证数据完整性**
5. **更新 .env.prod 中的 DATABASE_URL**

## 🔧 常用命令

### 查看 PostgreSQL 服务状态
```bash
sudo systemctl status postgresql
```

### 连接数据库
```bash
psql -U 用户名 -d 数据库名
```

### 查看所有表
```sql
\dt
```

### 查看表行数
```sql
SELECT COUNT(*) FROM 表名;
```

### 退出 psql
```sql
\q
```

## 📞 遇到问题？

请查看完整迁移指南：`MIGRATION_GUIDE.md`

包含详细的：
- 前提条件检查
- 完整迁移步骤
- 数据验证方法
- 故障排除指南
- 回滚方案
- 性能优化建议

---

**快速参考版本：** 1.0
**详细指南：** MIGRATION_GUIDE.md
**生成时间：** 2025-10-24
