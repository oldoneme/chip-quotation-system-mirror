# 网络环境切换指南

## 🚀 快速使用

### 自动检测并配置（推荐）
```bash
./scripts/network-env-manager.sh --auto
```

### 手动切换环境
```bash
# 切换到公司环境
./scripts/network-env-manager.sh --office

# 切换到家庭环境  
./scripts/network-env-manager.sh --home
```

### 查看当前状态
```bash
./scripts/network-env-manager.sh --status
```

## 📋 环境切换检查清单

每次更换网络环境时，请按以下步骤操作：

### 1. 检查当前状态
```bash
cd /home/qixin/projects/chip-quotation-system
./scripts/network-env-manager.sh --status
```

### 2. 配置网络环境
- **在公司**: `./scripts/network-env-manager.sh --office`
- **在家里**: `./scripts/network-env-manager.sh --home`
- **自动检测**: `./scripts/network-env-manager.sh --auto`

### 3. 验证配置
```bash
./scripts/network-env-manager.sh --test
```

### 4. 重启服务（如需要）
```bash
./scripts/network-env-manager.sh --restart
```

## ⚠️ 重要提醒

- **每次切换网络环境后必须运行配置命令**
- **如果前端出现loading问题，先检查网络配置**
- **如果API无法访问，运行 `--restart` 重启服务**

## 🔧 故障排除

### 前端一直loading
1. 运行: `./scripts/network-env-manager.sh --status`
2. 如果环境不匹配，运行相应的配置命令
3. 重启服务: `./scripts/network-env-manager.sh --restart`

### API访问失败
1. 检查后端是否启动: `curl http://127.0.0.1:8000`
2. 重启服务: `./scripts/network-env-manager.sh --restart`

## 📍 环境标识

- **公司环境**: 使用代理 (127.0.0.1:1080)
- **家庭环境**: 直连网络，无代理

---

💡 **小提示**: 将此文档加入书签，每次切换环境时参考使用！