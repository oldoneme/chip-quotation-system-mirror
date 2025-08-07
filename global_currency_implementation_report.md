# 全局币种设置功能实现报告

## 项目概述

根据用户需求，我们对系统进行了重新设计，将币种和汇率设置从板卡配置级别调整为机器级别。现在币种和汇率是全局设置，应用于该机器下的所有板卡配置。最终传递给报价页面的数据计算公式为：特定板卡的UnitPrice * 汇率 * 折扣率。

## 已完成的实现

### 1. 数据库模型更新

#### 1.1 Machine模型变更
- 在Machine实体中添加了[currency](file://d:\Projects\backend\app\schemas.py#L48-L48)字段，类型为String，默认值为"RMB"
- 保留了原有的[exchange_rate](file://d:\Projects\backend\app\schemas.py#L47-L47)字段，用于存储汇率
- 移除了CardConfig实体中的currency和exchange_rate字段

#### 1.2 数据库表结构
```python
class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    active = Column(Boolean, default=True)
    manufacturer = Column(String)
    discount_rate = Column(Float, default=1.0)
    exchange_rate = Column(Float, default=1.0)
    currency = Column(String, default="RMB")  # 币种: RMB 或 USD
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="machines")
    card_configs = relationship("CardConfig", back_populates="machine", cascade="all, delete-orphan")
```

### 2. API接口更新

#### 2.1 Machine Schemas更新
- 在MachineBase、MachineCreate和MachineUpdate schemas中添加了currency字段
- 设置了合理的默认值（currency默认为"RMB"）

#### 2.2 CardConfig Schemas更新
- 从CardConfigBase、CardConfigCreate和CardConfigUpdate schemas中移除了currency和exchange_rate字段

### 3. 前端界面更新

#### 3.1 机器模态框更新
- 添加了Currency选择框，支持RMB和USD两种选项
- 添加了动态显示的Exchange Rate输入框：
  - 当选择USD时，汇率输入框可编辑，默认值为7
  - 当选择RMB时，汇率输入框不可编辑，固定值为1

#### 3.2 机器列表显示优化
- 在机器列表项中添加了币种信息的显示

#### 3.3 板卡配置表格更新
- 更新了Unit Price列的显示逻辑：
  - 计算公式：UnitPrice * 汇率 * 折扣率
  - 根据机器的币种显示相应的货币符号（RMB显示¥，USD显示$）

#### 3.4 板卡配置模态框更新
- 移除了Currency选择框和Exchange Rate输入框

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

#### 动态汇率输入框
```javascript
<Form.Item
  noStyle
  shouldUpdate={(prevValues, currentValues) => prevValues.currency !== currentValues.currency}
>
  {({ getFieldValue }) => {
    const currency = getFieldValue('currency');
    return (
      <Form.Item
        name="exchange_rate"
        label="汇率"
        rules={[{ required: true, message: '请输入汇率!' }]}
      >
        <InputNumber 
          min={0} 
          step={0.01} 
          style={{ width: '100%' }} 
          disabled={currency === 'RMB'}
          defaultValue={currency === 'USD' ? 7 : 1}
        />
      </Form.Item>
    );
  }}
</Form.Item>
```

#### 表格价格计算逻辑
```javascript
render: (text, record) => {
  // 获取当前选中机器的币种和汇率
  const currency = selectedMachine?.currency || 'RMB';
  const exchangeRate = selectedMachine?.exchange_rate || 1;
  const discountRate = selectedMachine?.discount_rate || 1;
  
  // 计算最终价格: UnitPrice * 汇率 * 折扣率
  const finalPrice = record.unit_price * exchangeRate * discountRate;
  const currencySymbol = currency === 'USD' ? '$' : '¥';
  return `${currencySymbol}${finalPrice.toFixed(2)}`;
}
```

## 验证结果

### 数据库验证
1. ✅ Machines表已添加currency字段
2. ✅ CardConfig表已移除currency和exchange_rate字段
3. ✅ 相关外键关系保持不变

### API验证
1. ✅ GET /api/v1/machines/ 正常返回机器数据，包含currency字段
2. ✅ POST /api/v1/machines/ 支持currency字段的创建
3. ✅ PUT /api/v1/machines/{id} 支持currency字段的更新
4. ✅ GET /api/v1/card-configs/ 正常返回板卡配置数据，不包含currency和exchange_rate字段

### 前端验证
1. ✅ 机器列表正确显示币种信息
2. ✅ 机器添加/编辑模态框包含币种选择框
3. ✅ 当选择USD时，汇率输入框可编辑，默认值为7
4. ✅ 当选择RMB时，汇率输入框不可编辑，固定值为1
5. ✅ 板卡配置表格正确显示计算后的价格（UnitPrice * 汇率 * 折扣率）
6. ✅ 表单提交能正确保存币种和汇率数据

## 使用说明

### 如何为机器设置币种和汇率
1. 在设备型号列表中，点击"添加"按钮或选择现有机器进行编辑
2. 在机器模态框中，选择Currency（RMB或USD）
3. 根据选择的币种，系统会自动设置汇率：
   - 选择RMB时，汇率固定为1且不可编辑
   - 选择USD时，汇率默认为7，可以修改
4. 设置其他机器信息（如折扣率等）
5. 点击"确定"保存配置

### 价格计算规则
- 最终显示价格 = 板卡UnitPrice × 机器汇率 × 机器折扣率
- 根据机器币种显示相应货币符号（RMB显示¥，USD显示$）

## 总结

通过本次实现，我们成功将币种和汇率设置调整为机器级别的全局设置：
1. 币种和汇率现在是机器的属性，而不是每个板卡配置的属性
2. 支持人民币(RMB)和美元(USD)两种币种
3. USD币种下支持自定义汇率，默认值为7
4. RMB币种下汇率固定为1且不可编辑
5. 板卡配置表格正确显示基于机器设置计算后的价格
6. 保持了系统的完整功能和良好的用户体验

现在用户可以为每台机器设置统一的币种和汇率，该设置将应用于该机器下的所有板卡配置，简化了配置流程并提高了数据一致性。