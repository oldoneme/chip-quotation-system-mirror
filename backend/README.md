# 芯片测试报价系统 - 后端

## 📁 目录结构

```
backend/
├── app/                    # 应用主代码
│   ├── api/               # API路由
│   ├── models.py          # 数据库模型
│   ├── config.py          # 配置管理
│   ├── main.py            # FastAPI主应用
│   └── services/          # 业务逻辑服务
├── tests/                 # 测试文件
│   ├── test_simple_approval.py
│   ├── test_wecom_callback.py
│   └── test_complete_flow.py
├── scripts/               # 工具脚本
│   ├── create_approval_tables.py
│   ├── add_sample_data.py
│   └── check_tables.py
├── docs/                  # 文档
│   ├── WECOM_CALLBACK_CHECKLIST.md
│   └── WECOM_APPROVAL_USAGE.md
├── .env                   # 环境变量配置
├── .env.example           # 环境变量示例
├── requirements.txt       # Python依赖
├── init_data.py          # 初始化数据
├── sync_approval_daemon.py # 审批同步守护进程
└── monitor_approval.py   # 审批监控工具
```

## 🚀 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 初始化数据库
```bash
python3 init_data.py
python3 scripts/create_approval_tables.py
```

### 3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 文件，填入企业微信配置
```

### 4. 启动服务
```bash
# 开发环境
python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# 生产环境
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 5. 启动审批同步守护进程
```bash
python3 sync_approval_daemon.py
```

### 6. 安装 Playwright 与生成快照 PDF 自检
```bash
# 安装 Playwright 及 Chromium 依赖
pip install playwright
playwright install --with-deps chromium

# 使用快照 token 自检指定报价单页面
SNAP_TOKEN=<snapshot-jwt> python3 ../scripts/pw_selfcheck_snapshot.py CIS-KS20250101001
```

自检脚本会输出 `selfcheck_<QUOTE_NO>.png/pdf` 并打印结构化结果；它现在支持 `Authorization` / `auth_token` / `jwt` / `session_token` 多来源鉴权，用于验证 `quote-detail` 与 PDF 快照链路是否可达。

## 🧪 测试

### 运行测试
```bash
# 测试回调URL验证
python3 tests/test_wecom_callback.py

# 测试审批提交
python3 tests/test_simple_approval.py

# 测试完整流程
python3 tests/test_complete_flow.py
```

## 📋 核心功能

### ✅ 企业微信审批集成
- 审批申请提交
- 回调URL验证（GET /wecom/callback）
- 审批状态回调处理（POST /wecom/callback）
- ThirdNo映射支持
- 幂等性处理
- 自动状态同步

### ✅ 数据库表
- `quotes` - 报价单主表
- `approval_instance` - 审批实例映射
- `approval_timeline` - 回调事件时间线
- `users` - 用户表

### ✅ API端点
- `/api/v1/quotes` - 报价单管理
- `/api/v1/quotes/{id}/submit-approval` - 提交审批
- `/wecom/callback` - 企业微信回调
- `/api/v1/wecom-callback/simulate-approval` - 模拟审批（开发用）

## 🔧 工具脚本

- `scripts/create_approval_tables.py` - 创建审批相关数据库表
- `scripts/add_sample_data.py` - 添加示例数据
- `scripts/check_tables.py` - 检查数据库表结构
- `monitor_approval.py` - 监控审批状态变化
- `sync_approval_daemon.py` - 审批同步守护进程

## 📖 文档

- `docs/WECOM_CALLBACK_CHECKLIST.md` - 企业微信回调联调清单
- `docs/WECOM_APPROVAL_USAGE.md` - 审批系统使用指南

## 🌐 环境配置

主要环境变量：
```env
# 企业微信配置
FRONTEND_BASE_URL=https://your-frontend-domain
SNAPSHOT_BROWSER_POOL=3
SNAPSHOT_READY_SELECTOR=#quote-ready
WECOM_CORP_ID=企业ID
WECOM_AGENT_ID=应用ID  
WECOM_SECRET=应用密钥
WECOM_CALLBACK_TOKEN=回调验证Token
WECOM_ENCODING_AES_KEY=回调加密密钥

# 服务配置
API_BASE_URL=http://localhost:8000
DATABASE_URL=sqlite:///./app/test.db
DEBUG=True
```

## 📞 联系支持

如遇到问题，请查看：
1. `docs/` 目录下的相关文档
2. `tests/` 目录下的测试案例
3. 日志文件：`logs/` 目录

---
**更新时间**: 2025-09-03
**版本**: v1.0.0
