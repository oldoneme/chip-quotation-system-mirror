# 服务器部署配置指南

## 📋 部署环境说明

### 域名配置
- **开发环境**（本地PC）：`wecom-dev.chipinfos.com.cn`
- **生产环境**（公司服务器）：`wecom-quote.chipinfos.com.cn`

### 前提条件
- ✅ 代码已上传到服务器
- ✅ 服务器前后端服务可以正常启动
- ✅ 有 Cloudflare 账户访问权限

---

## 🎯 部署步骤总览

1. 配置 Cloudflare 隧道
2. 修改服务器后端配置文件
3. 更新企业微信管理后台配置
4. 重启服务器服务
5. 验证测试

---

## Step 1: 配置 Cloudflare 隧道

### 1.1 登录 Cloudflare 控制台

访问：https://dash.cloudflare.com/

### 1.2 进入 Cloudflare Tunnel 配置

导航路径：**Zero Trust** → **Access** → **Tunnels**

### 1.3 创建或修改隧道记录

#### 如果已有隧道（推荐）：
1. 找到现有的隧道
2. 点击「**Configure**」
3. 进入「**Public Hostname**」标签页

#### 添加新的公共主机名：
- **Subdomain**: `wecom-quote`
- **Domain**: `chipinfos.com.cn`
- **完整域名**: `wecom-quote.chipinfos.com.cn`
- **Type**: `HTTP`
- **URL**: `localhost:3000`（前端端口）

**重要配置**：
- ✅ 如果前端需要反向代理到后端，可能需要配置路径规则
- ✅ 确保隧道守护进程在服务器上正常运行

### 1.4 验证隧道连接

在服务器上检查隧道状态：
```bash
# 如果使用 cloudflared
cloudflared tunnel list
cloudflared tunnel info <tunnel-name>

# 检查隧道进程
ps aux | grep cloudflared
```

### 1.5 测试域名解析

```bash
# 在服务器上测试
curl https://wecom-quote.chipinfos.com.cn

# 应该能访问到前端页面
```

---

## Step 2: 修改服务器后端配置

### 2.1 登录到服务器

```bash
ssh your-server
```

### 2.2 进入项目目录

```bash
cd /path/to/chip-quotation-system/backend
```

### 2.3 备份原有配置

```bash
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)
```

### 2.4 编辑 .env 文件

```bash
vim .env
# 或使用其他编辑器: nano .env
```

### 2.5 修改以下 4 个配置项

找到并修改为生产环境域名：

```bash
# 修改前（开发环境）：
WECOM_CALLBACK_URL=https://wecom-dev.chipinfos.com.cn/wecom/callback
WECOM_BASE_URL=https://wecom-dev.chipinfos.com.cn
FRONTEND_BASE_URL=https://wecom-dev.chipinfos.com.cn
API_BASE_URL=https://wecom-dev.chipinfos.com.cn/api

# 修改后（生产环境）：
WECOM_CALLBACK_URL=https://wecom-quote.chipinfos.com.cn/wecom/callback
WECOM_BASE_URL=https://wecom-quote.chipinfos.com.cn
FRONTEND_BASE_URL=https://wecom-quote.chipinfos.com.cn
API_BASE_URL=https://wecom-quote.chipinfos.com.cn/api
```

**⚠️ 注意**：
- 保持路径部分不变（如 `/wecom/callback`、`/api`）
- 只替换域名部分：`wecom-dev` → `wecom-quote`
- 其他配置项（企业微信ID、密钥等）**保持不变**

### 2.6 保存并退出

- vim 编辑器：按 `ESC`，输入 `:wq`，按回车
- nano 编辑器：按 `Ctrl+X`，输入 `Y`，按回车

### 2.7 验证配置文件

```bash
# 检查配置文件中的域名
grep "chipinfos.com.cn" .env

# 应该看到 4 行，全部显示 wecom-quote.chipinfos.com.cn
```

---

## Step 3: 更新企业微信管理后台配置

### 3.1 登录企业微信管理后台

访问：https://work.weixin.qq.com/

### 3.2 进入应用管理

导航路径：**应用管理** → **自建** → **芯片测试报价系统**

### 3.3 修改应用主页

1. 点击「**应用主页**」旁边的「**修改**」
2. 修改为：`https://wecom-quote.chipinfos.com.cn`
3. 点击「**保存**」

### 3.4 修改网页授权域名

1. 点击「**网页授权及JS-SDK**」
2. 点击「**设置可信域名**」
3. 添加域名：`wecom-quote.chipinfos.com.cn`（不含 `https://`）
4. 按照提示下载验证文件（如需要）
   - 下载文件后上传到服务器的 `backend/app/static/` 目录
5. 点击「**确定**」

### 3.5 修改API接收消息URL（回调URL）

1. 点击「**接收消息**」→「**设置API接收**」
2. 修改 URL 为：`https://wecom-quote.chipinfos.com.cn/wecom/callback`
3. Token 保持不变：`cN9bXxcD80`
4. EncodingAESKey 保持不变：`S1iZ8DxsKGpiL3b10oVpRm59FphYwKzhtdSCR18q3nl`
5. 点击「**保存**」

**⚠️ 重要**：
- 企业微信会发送验证请求到你的服务器
- 确保后端服务正在运行
- 确保 Cloudflare 隧道已配置完成
- 如果验证失败，检查后端日志

---

## Step 4: 重启服务器上的服务

### 4.1 查找运行中的进程

```bash
# 检查后端进程
ps aux | grep uvicorn

# 检查前端进程
ps aux | grep "node.*react-scripts"
```

### 4.2 停止旧进程

#### 如果使用 screen 或 tmux：
```bash
# 后端
screen -r backend  # 或 tmux attach -t backend
Ctrl+C             # 停止服务

# 前端
screen -r frontend # 或 tmux attach -t frontend
Ctrl+C             # 停止服务
```

#### 如果直接运行：
```bash
# 找到进程ID
ps aux | grep uvicorn
ps aux | grep "node.*react-scripts"

# 停止进程
kill <进程ID>
```

### 4.3 启动新服务

#### 启动后端：
```bash
cd /path/to/chip-quotation-system/backend
source venv/bin/activate

# 使用 screen（推荐）
screen -S backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# 按 Ctrl+A 然后按 D 退出 screen 会话

# 或直接后台运行
nohup uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 > backend.log 2>&1 &
```

#### 启动前端：
```bash
cd /path/to/chip-quotation-system/frontend/chip-quotation-frontend

# 使用 screen（推荐）
screen -S frontend
PORT=3000 HOST=0.0.0.0 npm start
# 按 Ctrl+A 然后按 D 退出 screen 会话

# 或直接后台运行
nohup npm start > frontend.log 2>&1 &
```

### 4.4 验证服务启动

```bash
# 检查进程
ps aux | grep uvicorn
ps aux | grep "node.*react-scripts"

# 检查端口
netstat -tulpn | grep 8000
netstat -tulpn | grep 3000

# 查看后端启动日志
screen -r backend
# 应该看到：
# 🚀 启动应用，当前版本: xxxxxxx
# INFO:     Uvicorn running on http://0.0.0.0:8000
```

---

## Step 5: 验证配置

### 5.1 测试域名访问

在浏览器中打开：
```
https://wecom-quote.chipinfos.com.cn
```

应该能看到报价系统首页。

### 5.2 测试API接口

```bash
# 在服务器或本地测试
curl https://wecom-quote.chipinfos.com.cn/api/health
curl https://wecom-quote.chipinfos.com.cn/api/v1/machines/

# 应该返回正常的JSON响应
```

### 5.3 测试企业微信访问

1. 在企业微信移动端或PC端打开「芯片测试报价系统」应用
2. 检查是否能正常加载（应该显示新的生产环境）
3. 检查用户信息是否正确显示

### 5.4 测试完整功能流程

1. **创建测试报价单**
   - 选择报价类型
   - 添加设备和配置
   - 生成报价

2. **测试审批流程**
   - 提交审批
   - 检查企业微信是否收到审批通知
   - 在企业微信中打开审批链接
   - 完成审批操作

3. **检查回调功能**
   - 查看后端日志，应该能看到企业微信的回调请求
   ```bash
   screen -r backend
   # 或查看日志文件
   tail -f backend.log
   ```
   应该看到类似：
   ```
   2025-xx-xx xx:xx:xx - INFO - 收到企业微信回调请求
   2025-xx-xx xx:xx:xx - INFO - 审批结果已更新
   ```

### 5.5 验证PDF生成

1. 生成一个报价单的PDF
2. 检查PDF是否正确生成
3. 检查PDF中的链接是否指向正确的域名（`wecom-quote.chipinfos.com.cn`）

---

## ✅ 配置完成检查清单

### Cloudflare 配置
- [ ] Cloudflare 隧道已创建/更新
- [ ] 公共主机名 `wecom-quote.chipinfos.com.cn` 已添加
- [ ] 隧道指向正确的服务器和端口
- [ ] 隧道守护进程正在服务器上运行
- [ ] 域名解析正常（可以 ping 通）

### 服务器配置
- [ ] 服务器 `backend/.env` 文件已修改
- [ ] 4个域名相关配置都已更新为 `wecom-quote.chipinfos.com.cn`
- [ ] 配置文件备份已创建
- [ ] 后端服务已重启
- [ ] 前端服务已重启（如需要）

### 企业微信配置
- [ ] 应用主页已更新为 `https://wecom-quote.chipinfos.com.cn`
- [ ] 网页授权域名已更新为 `wecom-quote.chipinfos.com.cn`
- [ ] API回调URL已更新为 `https://wecom-quote.chipinfos.com.cn/wecom/callback`
- [ ] 回调URL验证通过

### 功能测试
- [ ] 浏览器可以访问前端页面
- [ ] API接口响应正常
- [ ] 企业微信中可以打开应用
- [ ] 报价单功能正常
- [ ] 审批流程正常
- [ ] 审批回调正常工作
- [ ] PDF生成功能正常

### 本地开发环境
- [ ] 本地PC的配置文件**保持不变**（仍然使用 `wecom-dev.chipinfos.com.cn`）
- [ ] 本地开发环境不受影响

---

## 🚨 常见问题

### Q1: Cloudflare 隧道连接失败

**现象**：访问 `wecom-quote.chipinfos.com.cn` 显示 502 或无法连接

**排查步骤**：
```bash
# 1. 检查 cloudflared 进程
ps aux | grep cloudflared

# 2. 检查隧道状态
cloudflared tunnel list
cloudflared tunnel info <tunnel-name>

# 3. 重启隧道
systemctl restart cloudflared
# 或手动启动
cloudflared tunnel run <tunnel-name>

# 4. 检查隧道日志
journalctl -u cloudflared -f
```

### Q2: 企业微信回调验证失败

**现象**：设置回调URL时提示验证失败

**排查步骤**：
1. 确认后端服务正在运行
2. 确认 Cloudflare 隧道已配置并连接
3. 测试回调URL是否可访问：
   ```bash
   curl https://wecom-quote.chipinfos.com.cn/wecom/callback
   ```
4. 查看后端日志中的详细错误信息
5. 确认 Token 和 EncodingAESKey 配置正确

### Q3: 前端可以访问，但API请求失败

**现象**：前端页面可以打开，但数据加载失败

**排查步骤**：
1. 检查浏览器控制台的网络请求
2. 确认API请求的域名是否正确
3. 检查 CORS 配置
4. 测试API接口：
   ```bash
   curl https://wecom-quote.chipinfos.com.cn/api/v1/machines/
   ```
5. 检查后端日志中的请求记录

### Q4: 如何回滚到之前的配置？

**回滚服务器配置**：
```bash
cd /path/to/chip-quotation-system/backend
# 恢复备份
cp .env.backup.YYYYMMDD_HHMMSS .env
# 重启后端服务
```

**回滚企业微信配置**：
- 在企业微信管理后台手动改回原来的配置

### Q5: 本地开发环境会受影响吗？

**A**: 不会！
- 本地PC的 `.env` 文件保持不变，仍然使用 `wecom-dev.chipinfos.com.cn`
- 服务器的 `.env` 文件使用 `wecom-quote.chipinfos.com.cn`
- 两个环境完全独立，互不影响

### Q6: 如何查看详细的错误日志？

```bash
# 后端日志
screen -r backend
# 或
tail -f /path/to/chip-quotation-system/backend/backend.log

# 前端日志
screen -r frontend
# 或
tail -f /path/to/chip-quotation-system/frontend/chip-quotation-frontend/frontend.log

# Cloudflare 隧道日志
journalctl -u cloudflared -f
```

---

## 📞 需要帮助？

如果遇到问题，按以下顺序排查：

1. **检查隧道连接**：确保 Cloudflare 隧道正常运行
2. **检查服务状态**：确保前后端服务正常运行
3. **检查日志**：查看详细的错误信息
4. **测试网络**：使用 curl 测试各个接口
5. **验证配置**：检查所有配置文件中的域名是否正确

---

## 🎉 部署成功标志

当你完成以下验证，说明部署成功：

✅ 在浏览器中访问 `https://wecom-quote.chipinfos.com.cn` 正常显示
✅ 在企业微信中打开应用正常显示
✅ 可以创建报价单
✅ 可以提交审批
✅ 企业微信收到审批通知
✅ 审批回调正常工作
✅ 本地开发环境不受影响

**恭喜！你的生产环境已成功部署！** 🎊
