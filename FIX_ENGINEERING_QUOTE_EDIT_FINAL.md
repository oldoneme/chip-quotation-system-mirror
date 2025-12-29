# 工程机时报价 - 增加调整报价及理由功能执行文档

## 目标
在工程机时报价单中，增加“调整价格”和“调整理由”字段。
规则：
1. 若 `调整后价格` >= `系统计算价格`，不需要理由。
2. 若 `调整后价格` < `系统计算价格`，必须填写理由。
3. **严格约束**：不改变或影响现有功能，仅增加新功能。其他报价类型（询价、工装）不受影响。
4. **新需求**：报价单详情页需同时展示：系统原价、调整后价格、调整理由。

## 任务列表

### Phase 1: 后端改造 (Backend)
- [ ] 1.1 修改 `backend/app/models.py`: 为 `QuoteItem` 添加 `adjusted_price` (Float) 和 `adjustment_reason` (Text) 字段。
- [ ] 1.2 创建并运行数据库迁移脚本 `add_columns.py` (针对 SQLite)。
- [ ] 1.3 修改 `backend/app/schemas.py`: 更新 `QuoteItemBase` 或 `QuoteItemCreate`/`QuoteItemResponse` 以支持新字段。

### Phase 2: 前端改造 - 确认报价页 (Frontend - QuoteResult)
- [ ] 2.1 修改 `frontend/chip-quotation-frontend/src/pages/QuoteResult.js`:
    - [ ] 仅针对 `quoteData.type === '工程报价'` (或 `engineering`) 的逻辑分支。
    - [ ] 将原有的费用列表展示改为可编辑的 `Table` 组件（或在现有结构中增加输入框）。
    - [ ] 增加状态 `engineeringItems` 来管理可编辑的行数据。
    - [ ] 实现校验逻辑：提交前检查 (调整价 < 原价 && 无理由)。
    - [ ] 提交时将新字段包含在 API Payload 中。

### Phase 3: 前端改造 - 详情页 (Frontend - QuoteDetail)
- [ ] 3.1 修改 `frontend/chip-quotation-frontend/src/pages/QuoteDetail.js`:
    - [ ] 仅针对工程机时报价的渲染逻辑。
    - [ ] 更新表格列定义，增加 "系统报价" (原 unit_price), "最终报价" (adjusted_price), "调整理由"。
    - [ ] 增加样式：如果发生调整，高亮显示差异。

### Phase 4: 验证与清理
- [ ] 4.1 启动前后端服务。
- [ ] 4.2 创建一个新的工程机时报价，测试高价调整（无理由）。
- [ ] 4.3 创建一个新的工程机时报价，测试低价调整（无理由 -> 拦截）。
- [ ] 4.4 创建一个新的工程机时报价，测试低价调整（有理由 -> 通过）。
- [ ] 4.5 验证详情页展示是否包含原价、现价和理由。
- [ ] 4.6 验证询价报价和工装报价是否未受影响。
- [ ] 4.7 清理迁移脚本。