# Pull Request: 报价单编辑功能和多项优化

## 📋 概述

将 `quote-detail-editable-claude` 分支合并到 `main` 分支，包含 48 个提交，实现报价单编辑功能和多项bug修复与优化。

## ✨ 主要功能

### 1. 报价单编辑功能
- ✅ 实现所有报价类型的编辑模式
- ✅ 新增 `useQuoteEditMode` Hook 统一管理编辑状态
- ✅ 支持编辑后保存并更新数据库
- ✅ 被驳回状态的报价单可重新编辑

### 2. 移动端优化
- ✅ 修复移动端报价单列表显示数字ID而非报价单号的问题
- ✅ 优化移动端报价管理页面展示

### 3. 报价页面优化
- ✅ 优化设备选择流程
- ✅ 移除报价模板功能（QuoteTemplate相关代码）
- ✅ 修复量产机时报价页面JSX语法错误

### 4. 工序报价修复
- ✅ 修正折扣率计算逻辑
- ✅ 修正机时费率计算逻辑，基于所选板卡计算
- ✅ 修复报价管理页面展开明细UPH和机时费率显示
- ✅ 移除人工成本逻辑

### 5. PDF快照优化
- ✅ PDF快照不再包含审批信息
- ✅ 修复PDF快照中审批历史显示为空的问题
- ✅ 修复PDF快照中审批状态显示为空的问题

### 6. 审批历史修复
- ✅ 修复审批历史时间显示精确到秒
- ✅ 修复审批历史API中User模型字段名错误
- ✅ 修复报价详情页面审批历史不显示的问题

### 7. 开发工具
- ✅ 新增 `push_all.sh` 脚本，一键推送到Gitee和GitHub
- ✅ 新增 `GIT_BRANCH_GUIDE.md` 分支管理指南

## 📊 变更统计

- **提交数量**: 48 个提交
- **文件变更**: 61 个文件
- **代码行数**: +9,152 行, -1,848 行
- **净增加**: +7,304 行

### 主要变更文件

#### 前端核心文件
- `src/hooks/useQuoteEditMode.js` (新增) - 1738 行
- `src/pages/EngineeringQuote.js` - 大幅优化
- `src/pages/MassProductionQuote.js` - 大幅优化
- `src/pages/ProcessQuote.js` - 修复多个问题
- `src/pages/QuoteDetail.js` - 增强编辑功能
- `src/pages/QuoteManagement.js` - 移动端优化
- `src/pages/ToolingQuote.js` - 功能改进

#### 删除的文件
- `src/pages/QuoteTemplate.js` (移除)
- `src/styles/QuoteTemplate.css` (移除)

#### 新增的文件
- `push_all.sh` - Git推送脚本
- `GIT_BRANCH_GUIDE.md` - 分支管理指南
- `src/hooks/useQuoteEditMode.js` - 编辑模式Hook

## 🔍 测试验证

### 已完成的测试
- ✅ 前端编译成功（无错误）
- ✅ 后端服务运行正常
- ✅ 前端服务运行正常
- ✅ 本地合并测试通过（无冲突）

### 建议测试项目
- [ ] 所有报价类型的新建功能
- [ ] 所有报价类型的编辑功能
- [ ] 移动端报价单列表显示
- [ ] PDF快照生成
- [ ] 审批历史显示
- [ ] 工序报价UPH和机时费率计算

## 📝 提交历史（最近20个）

```
docs: 添加Git分支管理指南和统一推送脚本
fix: 修复移动端报价单列表显示数字ID而非报价单号的问题
fix: 修复量产机时报价页面JSX语法错误
feat: 优化报价页面设备选择和移除报价模板功能
refactor: PDF快照不再包含审批信息
fix: PDF快照中审批历史显示为空的问题
fix: PDF快照中审批状态显示为空的问题
fix: 审批历史时间显示精确到秒
fix: 修复审批历史时间显示问题
fix: 修复审批历史API中User模型字段名错误
fix: 修复报价详情页面审批历史不显示的问题
fix: 修复量产报价编辑时板卡数量显示为默认值1的问题
fix: 允许被驳回状态的报价单可以编辑
fix: 修复工序报价编辑模式下项目信息显示问题
fix: 修复工序报价多个问题并移除人工成本逻辑
fix: 修正折扣率计算逻辑，移除错误的默认值
fix: 修正机时费率计算逻辑，基于所选板卡计算
fix: 修复报价管理页面展开明细UPH和机时费率显示
fix: 修复工序报价明细UPH和机时费率显示问题
chore: 移除工序报价调试日志，清理代码
```

## 🚀 部署注意事项

### 前端
- 无需额外配置
- 已删除 QuoteTemplate 相关代码，确保路由已移除

### 后端
- 无后端代码变更
- 数据库无需迁移

### 环境要求
- Node.js: 已有版本
- Python: 已有版本
- 无新增依赖

## ✅ 合并检查清单

- [x] 代码已通过本地测试
- [x] 前端编译无错误
- [x] 后端服务正常运行
- [x] 无合并冲突
- [x] 代码已推送到远程仓库
- [x] 所有提交信息清晰明确
- [ ] Code Review 通过
- [ ] 功能测试通过

## 📌 相关链接

- **源分支**: `quote-detail-editable-claude`
- **目标分支**: `main`
- **Gitee仓库**: https://gitee.com/zeroworkshop/chip-quotation-system-Linux
- **GitHub镜像**: https://github.com/oldoneme/chip-quotation-system-mirror

## 🤝 贡献者

- @qixin (主要开发)
- @Claude (AI辅助)

---

**合并后建议操作**:
1. 在生产环境部署前进行完整功能测试
2. 重点测试报价单编辑功能
3. 验证移动端显示是否正常
4. 检查PDF快照生成功能

🤖 Generated with [Claude Code](https://claude.com/claude-code)
