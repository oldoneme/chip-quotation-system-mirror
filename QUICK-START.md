# 🚀 项目快速启动指南

## ⚠️ 环境切换必读

**每次更换网络环境（公司 ↔ 家庭）时，请先运行：**

```bash
./scripts/network-env-manager.sh --auto
```

或者运行提醒脚本：
```bash
./scripts/reminder.sh
```

## 📋 启动检查清单

### 1. 网络环境配置 ✅
```bash
cd /home/qixin/projects/chip-quotation-system
./scripts/network-env-manager.sh --auto
```

### 2. 启动后端服务 ✅
```bash
cd backend
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 3. 启动前端服务 ✅
```bash
cd frontend/chip-quotation-frontend
npm start
```

### 4. 验证服务 ✅
- 前端: http://localhost:3000
- 后端API: http://localhost:8000
- API文档: http://localhost:8000/docs

## 🔧 常见问题

### 前端一直loading？
1. 检查网络配置：`./scripts/network-env-manager.sh --status`
2. 重新配置环境：`./scripts/network-env-manager.sh --auto`
3. 重启服务：`./scripts/network-env-manager.sh --restart`

### API无法访问？
1. 检查后端是否启动：`curl http://127.0.0.1:8000`
2. 重启服务：`./scripts/network-env-manager.sh --restart`

---

💡 **小贴士**: 将此文档置顶，每次启动项目前快速检查！