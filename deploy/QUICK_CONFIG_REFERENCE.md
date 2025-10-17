# 快速配置参考卡片

## 🌐 域名信息

- **开发环境**（本地PC）：`wecom-dev.chipinfos.com.cn`
- **生产环境**（服务器）：`wecom-quote.chipinfos.com.cn`

---

## 🎯 配置步骤速查

### 1. Cloudflare 隧道配置

**登录**：https://dash.cloudflare.com/

**路径**：Zero Trust → Access → Tunnels → Configure → Public Hostname

**添加配置**：
- Subdomain: `wecom-quote`
- Domain: `chipinfos.com.cn`
- Type: `HTTP`
- URL: `localhost:3000`

**验证命令**：
```bash
# 检查隧道状态
cloudflared tunnel list
ps aux | grep cloudflared

# 测试域名访问
curl https://wecom-quote.chipinfos.com.cn
```

---

### 2. 服务器 backend/.env 文件修改

需要修改 **4 个配置项**：

```bash
WECOM_CALLBACK_URL=https://wecom-quote.chipinfos.com.cn/wecom/callback
WECOM_BASE_URL=https://wecom-quote.chipinfos.com.cn
FRONTEND_BASE_URL=https://wecom-quote.chipinfos.com.cn
API_BASE_URL=https://wecom-quote.chipinfos.com.cn/api
```

**快速操作命令**：
```bash
# 登录服务器
ssh your-server

# 进入目录
cd /path/to/chip-quotation-system/backend

# 备份（带时间戳）
cp .env .env.backup.$(date +%Y%m%d_%H%M%S)

# 编辑（选择一个）
vim .env
nano .env

# 验证修改
grep "wecom-quote" .env
# 应该看到 4 行，都包含 wecom-quote.chipinfos.com.cn
```

---

### 3. 企业微信管理后台修改

**登录**：https://work.weixin.qq.com/

**路径**：应用管理 → 自建 → 芯片测试报价系统

#### 应用主页
```
https://wecom-quote.chipinfos.com.cn
```

#### 网页授权域名
```
wecom-quote.chipinfos.com.cn
```
（不含 `https://`）

#### API回调URL
```
URL: https://wecom-quote.chipinfos.com.cn/wecom/callback
Token: cN9bXxcD80
EncodingAESKey: S1iZ8DxsKGpiL3b10oVpRm59FphYwKzhtdSCR18q3nl
```

---

### 4. 重启服务

```bash
# 查找进程
ps aux | grep uvicorn
ps aux | grep "node.*react-scripts"

# 停止服务（如果使用 screen）
screen -r backend
Ctrl+C
screen -r frontend
Ctrl+C

# 重新启动后端
cd /path/to/chip-quotation-system/backend
source venv/bin/activate
screen -S backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
# Ctrl+A D 退出

# 重新启动前端
cd /path/to/chip-quotation-system/frontend/chip-quotation-frontend
screen -S frontend
PORT=3000 HOST=0.0.0.0 npm start
# Ctrl+A D 退出
```

---

## ✅ 验证检查

```bash
# 1. 测试域名访问
curl https://wecom-quote.chipinfos.com.cn

# 2. 测试API接口
curl https://wecom-quote.chipinfos.com.cn/api/health
curl https://wecom-quote.chipinfos.com.cn/api/v1/machines/

# 3. 检查服务进程
ps aux | grep uvicorn
ps aux | grep "node.*react-scripts"

# 4. 检查端口
netstat -tulpn | grep 8000
netstat -tulpn | grep 3000

# 5. 查看后端日志
screen -r backend
```

**浏览器测试**：
- 前端页面：https://wecom-quote.chipinfos.com.cn
- API文档：https://wecom-quote.chipinfos.com.cn/docs
- 企业微信应用：在企业微信中打开「芯片测试报价系统」

---

## 🚨 故障排查命令

### Cloudflare 隧道问题

```bash
# 检查隧道进程
ps aux | grep cloudflared

# 查看隧道列表和状态
cloudflared tunnel list
cloudflared tunnel info <tunnel-name>

# 重启隧道
systemctl restart cloudflared
# 或手动启动
cloudflared tunnel run <tunnel-name>

# 查看隧道日志
journalctl -u cloudflared -f
tail -f /var/log/cloudflared.log
```

### 后端服务问题

```bash
# 检查后端进程
ps aux | grep uvicorn

# 查看后端日志
screen -r backend
tail -f /path/to/backend/backend.log

# 测试后端API
curl http://localhost:8000/api/health
curl https://wecom-quote.chipinfos.com.cn/api/health
```

### 前端服务问题

```bash
# 检查前端进程
ps aux | grep "node.*react-scripts"

# 查看前端日志
screen -r frontend
tail -f /path/to/frontend/frontend.log

# 测试前端访问
curl http://localhost:3000
curl https://wecom-quote.chipinfos.com.cn
```

### 企业微信回调问题

```bash
# 测试回调URL可访问性
curl https://wecom-quote.chipinfos.com.cn/wecom/callback

# 查看后端日志中的回调记录
screen -r backend
# 查找包含 "wecom" 或 "callback" 的日志
```

### 网络连通性测试

```bash
# 测试域名解析
ping wecom-quote.chipinfos.com.cn
nslookup wecom-quote.chipinfos.com.cn

# 测试HTTPS连接
curl -I https://wecom-quote.chipinfos.com.cn

# 测试端口连通性
telnet localhost 8000
telnet localhost 3000
```

---

## 🔄 快速回滚

```bash
# 回滚配置文件
cd /path/to/chip-quotation-system/backend
ls .env.backup.*  # 查看可用备份
cp .env.backup.YYYYMMDD_HHMMSS .env

# 重启服务
# （参考上面的"重启服务"部分）
```

---

## 📝 配置检查清单

### Cloudflare
- [ ] 隧道已添加 `wecom-quote.chipinfos.com.cn`
- [ ] 隧道进程正在运行
- [ ] 域名可以访问

### 服务器
- [ ] backend/.env 已修改4个配置项
- [ ] 配置已备份
- [ ] 后端服务已重启
- [ ] 前端服务已重启

### 企业微信
- [ ] 应用主页已更新
- [ ] 网页授权域名已更新
- [ ] API回调URL已更新并验证通过

### 功能测试
- [ ] 前端页面可访问
- [ ] API接口正常响应
- [ ] 企业微信应用可打开
- [ ] 报价功能正常
- [ ] 审批流程正常

---

## 💡 重要提醒

### 环境隔离
- ✅ **本地PC**：继续使用 `wecom-dev.chipinfos.com.cn`，配置不需要修改
- ✅ **服务器**：使用 `wecom-quote.chipinfos.com.cn`，已完成配置
- ✅ 两个环境互不影响，可以同时运行

### 常见错误
- ❌ 忘记重启服务
- ❌ Cloudflare 隧道未启动
- ❌ 企业微信配置未更新
- ❌ 配置文件格式错误（多余空格、引号等）

### 必须操作
1. Cloudflare 隧道必须正常运行
2. 服务器 .env 必须修改4个配置项
3. 企业微信必须更新3个配置
4. 修改后必须重启后端服务

---

**提示**：完整的详细说明请参考 `SERVER_DEPLOYMENT_GUIDE.md`
