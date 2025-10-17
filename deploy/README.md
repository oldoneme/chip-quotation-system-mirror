# 部署配置文件说明

本目录包含服务器部署所需的配置文件和指南文档。

## 🌐 域名信息

- **开发环境**（本地PC）：`wecom-dev.chipinfos.com.cn`
- **生产环境**（公司服务器）：`wecom-quote.chipinfos.com.cn`

## 📁 文件列表

### 1. `production.env.template`
**用途**：服务器生产环境的 .env 配置文件模板

**使用方法**：
```bash
# 在服务器上：
cp production.env.template /path/to/backend/.env
# 然后编辑 .env，将 YOUR_SERVER_DOMAIN 替换为实际域名
```

### 2. `SERVER_DEPLOYMENT_GUIDE.md`
**用途**：详细的服务器部署配置指南

**包含内容**：
- Step by step 配置步骤
- 企业微信管理后台配置详解
- 服务重启方法
- 常见问题排查
- 完整的检查清单

**推荐**：第一次部署时完整阅读

### 3. `QUICK_CONFIG_REFERENCE.md`
**用途**：快速配置参考卡片

**包含内容**：
- 需要修改的配置项速查
- 常用命令速查
- 快速验证方法

**推荐**：熟悉部署流程后使用

---

## 🚀 快速开始

### 首次部署
1. 阅读 `SERVER_DEPLOYMENT_GUIDE.md`
2. 参考 `production.env.template` 修改服务器配置
3. 按照指南操作
4. 使用 `QUICK_CONFIG_REFERENCE.md` 进行验证

### 后续更新
1. 直接参考 `QUICK_CONFIG_REFERENCE.md`
2. 修改必要的配置项
3. 重启服务

---

## 📋 配置要点

### 需要在服务器修改的内容
服务器 `backend/.env` 文件中需要修改 **4 个配置项**，将域名改为 `wecom-quote.chipinfos.com.cn`：
- `WECOM_CALLBACK_URL`
- `WECOM_BASE_URL`
- `FRONTEND_BASE_URL`
- `API_BASE_URL`

### 不需要修改的内容
- 企业微信 ID、密钥
- Token、EncodingAESKey
- JWT 密钥
- 其他系统配置

### Cloudflare 隧道配置
需要在 Cloudflare 控制台添加新的公共主机名：`wecom-quote.chipinfos.com.cn`

### 企业微信管理后台
需要更新 **3 个配置项**为 `wecom-quote.chipinfos.com.cn`：
- 应用主页
- 网页授权域名
- API回调URL

### 本地开发环境
本地 PC 的 `backend/.env` 文件**保持不变**（仍然使用 `wecom-dev.chipinfos.com.cn`），不受服务器配置影响。

---

## ⚠️ 重要提示

1. **备份优先**：修改配置前先备份原文件
2. **服务重启**：配置修改后必须重启后端服务
3. **企业微信**：记得同步更新企业微信管理后台的配置
4. **验证测试**：配置完成后进行完整的功能测试

---

## 🔗 相关文档

- 项目开发文档：`../docs/`
- 工作流程说明：`../docs/WORKFLOW.md`
- 项目配置说明：`../.claude/CLAUDE.md`

---

## 📞 问题反馈

如遇到部署问题，请：
1. 查看后端日志获取详细错误信息
2. 参考 `SERVER_DEPLOYMENT_GUIDE.md` 中的常见问题部分
3. 检查企业微信管理后台的错误提示

---

**祝部署成功！** ✨
