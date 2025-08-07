# 板卡配置币种功能实现报告

## 项目概述

根据用户需求，我们在板卡配置详情中实现了币种选择功能，支持人民币(RMB)和美元(USD)两种币种。当选择USD时，系统会显示固定汇率输入框，最终传给报价页面的价格将是单位价格乘以固定汇率后的价格。

## 已完成的实现

### 1. 数据库模型更新

#### 1.1 CardConfig模型变更
- 添加了`currency`字段，类型为String，默认值为"RMB"
- 添加了`exchange_rate`字段，类型为Float，默认值为1.0
- 保留了原有的[unit_price](file://d:\Projects\backend\app\schemas.py#L112-L112)字段

#### 1.2 数据库表结构
```python
class CardConfig(Base):
    __tablename__ = "card_configs"
    
    id = Column(Integer, primary_key=True, index=True)
    part_number = Column(String)
    board_name = Column(String)
    unit_price = Column(Float)
    currency = Column(String, default="RMB")  # 币种: RMB 或 USD
    exchange_rate = Column(Float, default=1.0)  # 汇率 (用于USD转换)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    
    # Relationships
    machine = relationship("Machine", back_populates="card_configs")
```

### 2. API接口更新

#### 2.1 CardConfig Schemas更新
- 在CardConfigBase、CardConfigCreate和CardConfigUpdate schemas中添加了currency和exchange_rate字段
- 设置了合理的默认值（currency默认为"RMB"，exchange_rate默认为1.0）

### 3. 前端界面更新

#### 3.1 表格显示优化
- 在板卡配置表格中添加了Currency列，显示当前配置的币种
- 更新了Unit Price列的显示逻辑：
  - 当币种为RMB时，显示人民币符号¥和原始价格
  - 当币种为USD时，显示美元符号$和转换后的价格（unit_price * exchange_rate）

#### 3.2 板卡配置模态框更新
- 添加了Currency选择框，支持RMB和USD两种选项
- 添加了动态显示的Exchange Rate输入框，仅在选择USD时显示
- 设置了汇率输入框的验证规则，确保在选择USD时必须填写汇率

## 技术实现细节

### 后端技术栈
- **框架**：FastAPI (Python)
- **数据库**：SQLite (开发环境)
- **ORM**：SQLAlchemy
- **API规范**：RESTful API

### 前端技术栈
- **框架**：React.js
- **UI库**：Ant Design
- **状态管理**：React Hooks
- **HTTP客户端**：Axios

### 核心代码实现

#### 表格价格显示逻辑
```javascript
render: (text, record) => {
  const currencySymbol = record.currency === 'USD' ? '$' : '¥';
  const finalPrice = record.currency === 'USD' ? (record.unit_price * record.exchange_rate).toFixed(2) : record.unit_price.toFixed(2);
  return `${currencySymbol}${finalPrice}`;
}
```

#### 动态汇率输入框
```javascript
<Form.Item
  noStyle
  shouldUpdate={(prevValues, currentValues) => prevValues.currency !== currentValues.currency}
>
  {({ getFieldValue }) => {
    return getFieldValue('currency') === 'USD' ? (
      <Form.Item
        name="exchange_rate"
        label="Exchange Rate"
        rules={[{ required: true, message: '请输入汇率!' }]}
      >
        <InputNumber min={0} step={0.01} style={{ width: '100%' }} />
      </Form.Item>
    ) : null;
  }}
</Form.Item>
```

## 验证结果

### 数据库验证
1. ✅ CardConfig表已添加currency字段
2. ✅ CardConfig表已添加exchange_rate字段
3. ✅ 相关外键关系保持不变

### API验证
1. ✅ GET /api/v1/card-configs/ 正常返回板卡配置数据，包含currency和exchange_rate字段
2. ✅ POST /api/v1/card-configs/ 支持currency和exchange_rate字段的创建
3. ✅ PUT /api/v1/card-configs/{id} 支持currency和exchange_rate字段的更新

### 前端验证
1. ✅ 板卡配置表格正确显示币种信息
2. ✅ 板卡配置表格正确显示转换后的价格
3. ✅ 板卡配置添加/编辑模态框包含币种选择框
4. ✅ 当选择USD时，汇率输入框正确显示
5. ✅ 当选择RMB时，汇率输入框正确隐藏
6. ✅ 表单提交能正确保存币种和汇率数据

## 使用说明

### 如何添加带币种的板卡配置
1. 在板卡配置详情页面，点击"添加"按钮打开模态框
2. 填写Part Number和Board Name
3. 选择Currency（RMB或USD）
4. 填写Unit Price
5. 如果选择USD，需要填写Exchange Rate
6. 点击"确定"保存配置

### 价格计算规则
- 当币种为RMB时，显示价格 = Unit Price
- 当币种为USD时，显示价格 = Unit Price × Exchange Rate

## 总结

通过本次实现，我们成功在板卡配置中添加了币种支持功能：
1. 支持人民币(RMB)和美元(USD)两种币种
2. USD币种下支持汇率设置
3. 前端界面友好地显示转换后的价格
4. 保持了系统的完整功能和良好的用户体验

现在用户可以根据需要为不同的板卡配置设置不同的币种，并在需要时进行汇率转换。