# 数据库迁移指南

## 📊 数据库信息

### 本地数据库状态
- **文件路径**: `backend/app/test.db`
- **文件大小**: 456KB
- **数据库类型**: SQLite 3
- **记录总数**:
  - 报价单: 87条
  - 报价项目: 195条
  - 用户: 7个
  - 设备: 8台
  - 审批记录: 106条
  - 其他配置数据

---

## 🎯 迁移方案

### 方案说明
由于使用的是 SQLite 文件型数据库，迁移非常简单：
1. 备份本地数据库
2. 将数据库文件传输到服务器
3. 验证服务器数据库
4. 重启服务器后端服务

---

## 📋 Step 1: 备份本地数据库

### 在本地 PC 上执行：

```bash
# 进入项目目录
cd /home/qixin/projects/chip-quotation-system/backend/app

# 创建备份（带时间戳）
cp test.db test.db.backup.$(date +%Y%m%d_%H%M%S)

# 验证备份
ls -lh test.db*
```

**预期输出**：
```
-rw-r--r-- 1 qixin qixin 456K Oct 11 16:21 test.db
-rw-r--r-- 1 qixin qixin 456K Oct 17 10:30 test.db.backup.20251017_103000
```

---

## 📤 Step 2: 传输数据库到服务器

### 方法1：使用 SCP（推荐）

在本地 PC 上执行：

```bash
# 传输数据库文件到服务器
scp /home/qixin/projects/chip-quotation-system/backend/app/test.db \
    your-user@your-server:/path/to/chip-quotation-system/backend/app/test.db

# 示例（请替换为实际的服务器信息）：
# scp backend/app/test.db root@192.168.1.100:/opt/chip-quotation-system/backend/app/test.db
```

### 方法2：使用 rsync（更安全，支持断点续传）

```bash
# 使用 rsync 传输
rsync -avz --progress \
    /home/qixin/projects/chip-quotation-system/backend/app/test.db \
    your-user@your-server:/path/to/chip-quotation-system/backend/app/test.db
```

### 方法3：如果服务器和本地在同一网络

如果你的服务器可以访问你的本地 PC，可以在服务器上执行：

```bash
# 在服务器上执行
cd /path/to/chip-quotation-system/backend/app
scp your-local-user@your-local-ip:/home/qixin/projects/chip-quotation-system/backend/app/test.db ./test.db
```

---

## 🔍 Step 3: 验证服务器数据库

### 在服务器上执行：

```bash
# 检查文件是否存在
ls -lh /path/to/chip-quotation-system/backend/app/test.db

# 检查文件大小（应该约为 456KB）
du -h /path/to/chip-quotation-system/backend/app/test.db

# 验证数据库完整性
python3 << 'EOF'
import sqlite3
conn = sqlite3.connect('/path/to/chip-quotation-system/backend/app/test.db')
cursor = conn.cursor()

# 统计数据
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name;")
tables = cursor.fetchall()
print('数据库表和记录数:')
total_records = 0
for table in tables:
    cursor.execute(f'SELECT COUNT(*) FROM {table[0]}')
    count = cursor.fetchone()[0]
    total_records += count
    if count > 0:
        print(f'  {table[0]}: {count}条')

print(f'\n总记录数: {total_records}')

# 验证关键表
cursor.execute("SELECT COUNT(*) FROM quotes")
quotes_count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM users")
users_count = cursor.fetchone()[0]

print(f'\n关键数据验证:')
print(f'  报价单: {quotes_count}条')
print(f'  用户: {users_count}个')

conn.close()
print('\n✅ 数据库验证完成')
EOF
```

**预期输出**：
```
数据库表和记录数:
  quotes: 87条
  quote_items: 195条
  users: 7条
  machines: 8条
  ...

关键数据验证:
  报价单: 87条
  用户: 7个

✅ 数据库验证完成
```

---

## 🔄 Step 4: 重启服务器后端服务

数据库文件传输完成后，需要重启后端服务：

```bash
# 方法1：如果使用 screen
screen -r backend
# 按 Ctrl+C 停止
# 重新启动
cd /path/to/chip-quotation-system/backend
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 按 Ctrl+A D 退出

# 方法2：如果使用 systemd
sudo systemctl restart chip-quotation-backend

# 方法3：杀进程重启
ps aux | grep uvicorn
kill <进程ID>
# 然后启动服务
```

---

## ✅ Step 5: 验证服务器应用

### 检查后端日志

```bash
# 查看后端日志
screen -r backend
# 应该看到：
# 🚀 启动应用，当前版本: xxxxxxx
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 测试数据访问

```bash
# 测试API接口
curl https://wecom-quote.chipinfos.com.cn/api/v1/quotes/stats

# 应该返回包含 87 条报价的统计信息
```

### 在企业微信中测试

1. 打开企业微信应用
2. 查看报价单列表 - 应该能看到 87 条报价
3. 查看用户信息 - 应该能看到 7 个用户
4. 测试创建新报价单功能

---

## 🚨 常见问题

### Q1: 传输后数据库文件权限错误

**现象**: 服务器日志显示 "Permission denied"

**解决**:
```bash
# 修改数据库文件所有者
sudo chown your-user:your-user /path/to/chip-quotation-system/backend/app/test.db

# 修改权限
chmod 644 /path/to/chip-quotation-system/backend/app/test.db
```

### Q2: 数据库被锁定

**现象**: 服务器日志显示 "database is locked"

**解决**:
```bash
# 停止所有访问数据库的进程
ps aux | grep uvicorn
kill <进程ID>

# 重新启动服务
```

### Q3: 传输后数据丢失

**原因**: 传输过程中文件损坏

**解决**:
```bash
# 使用校验和验证文件完整性

# 在本地计算 MD5
md5sum /home/qixin/projects/chip-quotation-system/backend/app/test.db

# 在服务器上计算 MD5
md5sum /path/to/chip-quotation-system/backend/app/test.db

# 两个 MD5 值应该完全一致
```

### Q4: 服务器显示空数据库

**可能原因**:
1. 传输的文件路径不对
2. 服务器 .env 配置的数据库路径不对

**检查**:
```bash
# 检查服务器 .env 中的数据库配置
cd /path/to/chip-quotation-system/backend
cat .env | grep DATABASE_URL

# 应该显示：
# DATABASE_URL=sqlite:///./app/test.db

# 确认文件位置
ls -lh app/test.db
```

---

## 🔒 安全建议

### 1. 定期备份

在服务器上设置自动备份：

```bash
# 创建备份脚本
cat > /path/to/chip-quotation-system/deploy/backup-db.sh << 'EOF'
#!/bin/bash
BACKUP_DIR="/path/to/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR
cp /path/to/chip-quotation-system/backend/app/test.db \
   $BACKUP_DIR/test.db.backup.$DATE
# 保留最近7天的备份
find $BACKUP_DIR -name "test.db.backup.*" -mtime +7 -delete
EOF

chmod +x /path/to/chip-quotation-system/deploy/backup-db.sh

# 添加到 crontab（每天凌晨2点备份）
# crontab -e
# 0 2 * * * /path/to/chip-quotation-system/deploy/backup-db.sh
```

### 2. 传输加密

如果数据敏感，使用加密传输：

```bash
# 使用 gpg 加密
gpg -c backend/app/test.db
# 生成 test.db.gpg

# 传输加密文件
scp backend/app/test.db.gpg your-server:/path/

# 在服务器上解密
gpg -d test.db.gpg > test.db
```

---

## 📝 迁移检查清单

- [ ] 本地数据库已备份
- [ ] 数据库文件已传输到服务器
- [ ] 服务器数据库文件权限正确
- [ ] 数据库完整性验证通过
- [ ] 服务器后端服务已重启
- [ ] 企业微信应用能正常访问数据
- [ ] 用户可以看到历史报价单
- [ ] 新建报价单功能正常

---

## 🎉 迁移完成

当所有检查清单都完成后，数据库迁移成功！

- ✅ 本地开发环境继续使用原数据库
- ✅ 服务器生产环境使用迁移后的数据库
- ✅ 两个环境数据独立，互不影响

**后续建议**:
1. 设置定期备份计划
2. 监控数据库文件大小
3. 定期清理过期数据（如旧的 session 记录）
