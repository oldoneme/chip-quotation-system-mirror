# 企业微信审批集成指南

## 概述

本系统支持将报价单审批流程集成到企业微信审批系统中，实现自动化审批管理。当企业微信审批不可用时，系统会自动回退到本地审批模式。

## 功能特性

- ✅ 自动提交报价单到企业微信审批
- ✅ 实时同步审批状态
- ✅ 审批历史记录追踪
- ✅ 自动回退到本地审批
- ✅ 审批结果回调处理
- ✅ 灵活的审批流程配置

## 配置步骤

### 1. 企业微信应用配置

1. 登录企业微信管理后台
2. 创建自建应用或使用现有应用
3. 获取以下信息：
   - `CORP_ID`: 企业ID
   - `AGENT_ID`: 应用ID
   - `CORP_SECRET`: 应用Secret

### 2. 创建审批模板

1. 在企业微信管理后台 → 应用与小程序 → 审批
2. 创建自定义审批模板
3. 配置以下字段：
   - 报价单号（文本）
   - 报价标题（文本）
   - 客户名称（文本）
   - 报价类型（文本）
   - 报价总金额（金额）
   - 报价明细（多行文本）
   - 备注说明（多行文本）
4. 记录模板ID

### 3. 环境变量配置

在系统环境变量或 `.env` 文件中设置：

```bash
# 企业微信基础配置
WECOM_CORP_ID=your_corp_id_here
WECOM_AGENT_ID=your_agent_id_here  
WECOM_CORP_SECRET=your_corp_secret_here

# 审批模板ID
WECOM_QUOTE_TEMPLATE_ID=your_template_id_here

# 可选：审批超时时间（小时，默认24）
WECOM_APPROVAL_TIMEOUT_HOURS=24
```

### 4. 回调URL配置

在企业微信管理后台配置审批结果回调URL：
```
https://your-domain.com/api/v1/wecom-approval/callback
```

## API接口

### 审批状态查询
```http
GET /api/v1/wecom-approval/status/{quote_id}
```

### 审批历史记录
```http
GET /api/v1/wecom-approval/history/{quote_id}
```

### 手动同步状态
```http
POST /api/v1/wecom-approval/sync/{quote_id}
```

### 审批回调接口
```http
POST /api/v1/wecom-approval/callback
```

## 工作流程

### 审批提交流程

1. **用户提交审批**
   ```http
   POST /api/v1/quotes/{quote_id}/submit
   ```

2. **系统处理逻辑**
   ```
   检查企业微信配置 → 构建审批数据 → 调用企业微信API
   ↓
   成功: 更新报价单状态为pending，记录wecom_approval_id
   ↓
   失败: 回退到本地审批，状态更新为pending
   ```

3. **审批结果处理**
   - 通过回调自动更新状态
   - 手动同步状态查询
   - 本地状态管理

### 状态映射

| 企业微信状态 | 本地状态 | 说明 |
|-------------|---------|------|
| 1 | pending | 审批中 |
| 2 | approved | 已同意 |
| 3 | rejected | 已驳回 |
| 4 | cancelled | 已撤销 |

## 故障处理

### 常见问题

1. **企业微信API调用失败**
   - 自动回退到本地审批
   - 记录错误日志
   - 提示用户使用本地审批

2. **审批模板配置错误**
   - 检查模板ID是否正确
   - 验证字段配置是否匹配

3. **网络连接问题**
   - 自动重试机制
   - 回退到本地审批

### 监控和日志

系统会记录以下关键信息：
- 审批提交日志
- API调用状态
- 错误信息和回退原因
- 审批状态变更历史

## 测试验证

### 功能测试

1. **创建测试报价单**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/quotes/" \
     -H "Content-Type: application/json" \
     -d '{...}'
   ```

2. **提交审批测试**
   ```bash
   curl -X POST "http://localhost:8000/api/v1/quotes/{id}/submit"
   ```

3. **状态查询测试**
   ```bash
   curl -X GET "http://localhost:8000/api/v1/wecom-approval/status/{quote_id}"
   ```

### 配置验证

- 确认环境变量正确设置
- 验证企业微信API连通性
- 测试审批模板数据格式
- 验证回调URL可访问性

## 安全考虑

- 使用HTTPS传输审批数据
- 验证回调请求来源
- 敏感信息加密存储
- 审批权限控制
- 操作日志记录

## 升级和维护

- 定期更新企业微信API版本
- 监控审批流程性能
- 备份审批历史数据
- 测试故障恢复流程

---

更多技术支持请查看企业微信开发文档：https://developer.work.weixin.qq.com/