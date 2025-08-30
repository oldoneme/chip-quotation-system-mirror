# 企业微信审批系统测试清单

## 📱 前端UI测试

### 1. 报价详情页面测试
访问 http://localhost:3000/quote-detail/31

**预期结果：**
- ✅ 页面正常加载，显示报价单基本信息
- ✅ 页面底部应该显示"审批操作"面板（如果有审批权限）
- ✅ 页面底部应该显示"审批历史"组件
- ✅ 移动端响应式布局正常

**测试步骤：**
```bash
# 1. 在浏览器中访问
http://localhost:3000/quote-detail/31

# 2. 检查开发者工具Console是否有错误
# 3. 调整浏览器窗口大小测试响应式
# 4. 检查审批面板和历史组件是否渲染
```

### 2. 企业微信审批页面测试
访问 http://localhost:3000/approval/a1sfcAgQsX8qtVryGnp7kgTpo3oBXFiZ

**预期结果：**
- ✅ 页面加载，显示"企业微信审批"标题
- ✅ 显示报价单基本信息
- ✅ 显示审批操作按钮（批准、拒绝等）
- ✅ 移动端优化布局

## 🔧 后端API功能测试

### 3. 完整审批流程测试

```bash
# Step 1: 生成审批链接
curl -X POST http://127.0.0.1:8000/api/v1/wecom-approval/generate-approval-link/31

# Step 2: 使用返回的token访问审批信息
curl -X GET http://127.0.0.1:8000/api/v1/wecom-approval/approval-link/{返回的token}

# Step 3: 测试各种审批操作（会因为权限失败，这是正常的）
curl -X POST http://127.0.0.1:8000/api/v1/wecom-approval/approve/31 \
  -H "Content-Type: application/json" \
  -d '{"comments": "测试批准操作"}'
```

### 4. 数据库一致性测试

```bash
# 检查审批链接是否正确存储
cd /home/qixin/projects/chip-quotation-system/backend
python3 -c "
import sqlite3
conn = sqlite3.connect('app/test.db')
cursor = conn.cursor()
cursor.execute('SELECT id, approval_link_token FROM quotes WHERE id = 31')
result = cursor.fetchone()
print(f'报价单31的审批Token: {result}')
conn.close()
"
```

## 🌐 网络和路由测试

### 5. 路由可达性测试
```bash
# 测试所有新增的API端点
curl -I http://127.0.0.1:8000/api/v1/wecom-approval/status/31
curl -I http://127.0.0.1:8000/api/v1/wecom-approval/history/31
# ... 其他端点
```

## 📱 移动端兼容性测试

### 6. 响应式设计测试
- 在不同屏幕尺寸下测试（手机、平板、桌面）
- 检查按钮和文本的可读性
- 验证触摸目标大小

## 🔐 安全性测试

### 7. 权限和验证测试
```bash
# 测试无效Token
curl -X GET http://127.0.0.1:8000/api/v1/wecom-approval/approval-link/invalid-token

# 测试过期或不存在的资源
curl -X GET http://127.0.0.1:8000/api/v1/wecom-approval/status/999999
```

## ❌ 预期的测试结果

### 正常情况：
- API返回正确的JSON响应
- 前端页面正常渲染组件
- 移动端布局适配良好

### 错误情况：
- 无效请求返回适当的HTTP错误码
- 前端显示友好的错误提示
- 不会导致系统崩溃

## 🚨 需要注意的限制

**当前测试限制：**
1. 审批操作需要用户认证（目前会返回权限错误）
2. 企业微信集成功能需要配置后才能完全测试
3. 某些高级功能需要实际的企业微信环境

**测试建议：**
- 重点测试UI组件渲染和响应式设计
- 验证API端点的可达性和错误处理
- 确保没有JavaScript错误或网络请求失败