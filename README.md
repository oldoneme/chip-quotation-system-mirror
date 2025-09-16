# 芯片报价系统

## 📚 项目文档导航

本项目的文档已按类型整理，便于查询：

### 🔍 快速导航

| 需求 | 目录 | 说明 |
|------|------|------|
| **了解项目进度** | [`docs/reports/`](docs/reports/) | Step完成报告和里程碑 |
| **学习系统使用** | [`docs/guides/`](docs/guides/) | 用户操作指南 |
| **查看项目规划** | [`docs/project/`](docs/project/) | 实施计划和时间线 |
| **部署到生产** | [`docs/deployment/`](docs/deployment/) | 部署配置和设置 |
| **查看测试结果** | [`docs/testing/`](docs/testing/) | 测试报告和验证 |
| **了解API接口** | [`docs/api/`](docs/api/) | API文档和开发指南 |

### 📋 主要功能

- ✅ **芯片测试报价计算** - 基于设备配置的自动化报价
- ✅ **统一审批系统** - 企业微信 + 内部审批双重支持
- ✅ **用户权限管理** - 多角色权限控制
- ✅ **实时状态同步** - 审批状态实时更新
- ✅ **移动端支持** - 企业微信移动端适配

### 🚀 快速开始

1. **启动后端服务**:
   ```bash
   cd backend
   python3 -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

2. **启动前端服务**:
   ```bash
   cd frontend/chip-quotation-frontend
   npm start
   ```

3. **查看用户指南**:
   - 📖 [统一审批系统用户指南](docs/guides/STEP6_UNIFIED_APPROVAL_USER_GUIDE.md)

### 📊 项目状态

- **当前版本**: v1.0
- **开发状态**: ✅ 已完成
- **系统质量**: 86.7/100 (优秀)
- **文档完整性**: 95% (优秀)
- **测试覆盖**: 全面测试通过

### 🛠️ 技术栈

- **后端**: Python + FastAPI + SQLAlchemy
- **前端**: React + Ant Design + TypeScript
- **数据库**: PostgreSQL (生产) / SQLite (开发)
- **认证**: 企业微信 OAuth
- **部署**: Docker + Nginx (推荐)

---

📄 **详细文档**: 查看 [`docs/`](docs/) 目录获取完整文档
🔧 **配置说明**: 查看 [`CLAUDE.md`](CLAUDE.md) 了解开发配置
