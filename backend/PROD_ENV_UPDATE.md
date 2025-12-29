# .env.prod 数据库配置更新指南

## 概述

迁移到 PostgreSQL 后，需要更新服务器上的 `.env.prod` 文件，将 `DATABASE_URL` 从 SQLite 改为 PostgreSQL 连接字符串。

## 当前配置（迁移前）

```bash
# —— 数据库配置（生产环境）——
DATABASE_URL=sqlite:///./data/prod/app.db
```

## 需要更新为（迁移后）

```bash
# —— 数据库配置（生产环境）——
DATABASE_URL=postgresql://用户名:密码@localhost:5432/数据库名
```

## PostgreSQL 连接字符串格式

```
postgresql://[用户名]:[密码]@[主机地址]:[端口]/[数据库名]
```

参数说明：
- **用户名**: PostgreSQL 用户名（例如：chip_user）
- **密码**: PostgreSQL 密码
- **主机地址**: 通常为 localhost（如果数据库在同一服务器）
- **端口**: 默认 5432
- **数据库名**: 数据库名称（例如：chip_quotation）

## 示例配置

### 示例 1: 本地 PostgreSQL

```bash
DATABASE_URL=postgresql://chip_user:StrongPassword123@localhost:5432/chip_quotation
```

### 示例 2: 远程 PostgreSQL

```bash
DATABASE_URL=postgresql://chip_user:StrongPassword123@192.168.1.100:5432/chip_quotation
```

### 示例 3: 使用 Unix Socket

```bash
DATABASE_URL=postgresql://chip_user:StrongPassword123@/chip_quotation
```

## 操作步骤

### 步骤 1: 在服务器上编辑 .env.prod

```bash
# SSH 登录到服务器
ssh 用户名@服务器IP

# 进入项目目录
cd /path/to/chip-quotation-system

# 编辑 .env.prod
nano .env.prod
```

### 步骤 2: 更新 DATABASE_URL

找到以下行：
```bash
DATABASE_URL=sqlite:///./data/prod/app.db
```

替换为：
```bash
DATABASE_URL=postgresql://your_db_user:your_password@localhost:5432/your_db_name
```

**注意**: 请替换以下占位符为实际值：
- `your_db_user`: 你的 PostgreSQL 用户名
- `your_password`: 你的 PostgreSQL 密码
- `your_db_name`: 你的数据库名称

### 步骤 3: 保存文件

- nano 编辑器：按 `Ctrl+O` 保存，`Ctrl+X` 退出
- vim 编辑器：按 `Esc`，输入 `:wq`，回车

### 步骤 4: 验证配置

测试数据库连接：

```bash
cd backend
source venv/bin/activate
python3 << 'EOF'
from app.database import engine
try:
    with engine.connect() as conn:
        result = conn.execute("SELECT 1")
        print("✅ 数据库连接成功！")
except Exception as e:
    print(f"❌ 数据库连接失败: {e}")
EOF
```

### 步骤 5: 重启后端服务

```bash
# 停止现有服务
pkill -f uvicorn

# 使用 .env.prod 启动服务
cd backend
source venv/bin/activate
uvicorn app.main:app --host 0.0.0.0 --port 8000 --env-file ../.env.prod
```

## 其他需要更新的占位符

除了 `DATABASE_URL`，`.env.prod` 中还有以下占位符需要替换：

```bash
# 企业微信应用凭证（正式版应用）
WECOM_AGENT_ID=__PROD_AGENT_ID__           # ← 需要更新
WECOM_SECRET=__PROD_SECRET__               # ← 需要更新
WECOM_CORP_SECRET=__PROD_SECRET__          # ← 需要更新

# 企业微信回调配置
WECOM_CALLBACK_TOKEN=__PROD_TOKEN__        # ← 需要更新
WECOM_ENCODING_AES_KEY=__PROD_AESKEY_43_CHARS__  # ← 需要更新

# JWT 配置
SECRET_KEY=__PROD_JWT_SECRET_CHANGE_ME__   # ← 需要更新
DEEPLINK_JWT_SECRET=__PROD_DEEPLINK_SECRET_CHANGE_ME__  # ← 需要更新
```

## 安全建议

1. **使用强密码**
   - 数据库密码至少 16 字符
   - 包含大小写字母、数字和特殊字符

2. **限制数据库访问**
   ```bash
   # 在 PostgreSQL 中只允许本地连接
   # 编辑 /etc/postgresql/版本/main/pg_hba.conf
   # 添加：
   local   chip_quotation   chip_user   md5
   ```

3. **定期备份数据库**
   ```bash
   pg_dump chip_quotation | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

4. **不要将 .env.prod 提交到 Git**
   - 已在 .gitignore 中配置忽略
   - 确认：`git status` 应该看不到 .env.prod

## 常见问题

### Q: 如何生成安全的 SECRET_KEY？

```bash
# 方法 1: 使用 Python
python3 -c "import secrets; print(secrets.token_urlsafe(64))"

# 方法 2: 使用 OpenSSL
openssl rand -base64 64 | tr -d '\n'
```

### Q: 忘记 PostgreSQL 密码怎么办？

```bash
# 使用 postgres 用户重置密码
sudo -u postgres psql
ALTER USER chip_user WITH PASSWORD 'new_password';
\q
```

### Q: 如何测试 PostgreSQL 连接？

```bash
# 使用 psql 命令测试
psql -U chip_user -d chip_quotation -h localhost -p 5432
# 输入密码后应该能连接成功
```

### Q: 服务启动后还是连接 SQLite 怎么办？

检查以下几点：
1. 确认 .env.prod 文件路径正确
2. 确认启动命令包含 `--env-file ../.env.prod`
3. 检查 backend/app/database.py 是否正确读取环境变量
4. 重启服务确保配置生效

## 验证迁移成功

迁移完成后，执行以下验证：

```bash
# 1. 检查数据库中的数据
psql -U chip_user -d chip_quotation -c "
SELECT
    (SELECT COUNT(*) FROM users) as users,
    (SELECT COUNT(*) FROM quotes) as quotes,
    (SELECT COUNT(*) FROM quote_items) as quote_items;
"

# 预期输出：
#  users | quotes | quote_items
# -------+--------+-------------
#      7 |     87 |         195

# 2. 测试 API 接口
curl http://服务器IP:8000/api/v1/quotes/stats

# 3. 在企业微信中测试完整流程
#    - 创建新报价单
#    - 提交审批
#    - 查看历史记录
```

---

**更新时间**: 2025-10-24
**相关文档**: MIGRATION_GUIDE.md, QUICK_MIGRATION_STEPS.md
