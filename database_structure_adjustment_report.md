# 数据库结构调整报告

## 项目概述

根据用户需求，我们对芯片测试报价系统的数据库结构进行了调整。主要变更包括：
1. 在设备型号（Machine）中保留并正确显示"固定折扣率"（discount_rate）字段
2. 移除设备型号中的基础配置，所有配置都定义在对应的板卡配置详情中

## 已完成的调整

### 1. 数据库模型确认

经过检查，数据库模型已经符合要求：
- Machine实体中已包含`discount_rate`字段，类型为Float，默认值为1.0
- 已移除不必要的配置实体（Configuration），所有配置信息都通过CardConfig实体管理
- 保持了四层结构：
  1. 机器类型（MachineType）
  2. 供应商（Supplier）
  3. 机器型号（Machine）
  4. 板卡配置（CardConfig）

### 2. 前端界面更新

#### 2.1 机器模态框更新
- 在机器添加/编辑模态框中添加了"固定折扣率"字段输入项
- 设置了合理的输入限制（0-1之间的数值，步长为0.01）
- 添加了字段验证规则

#### 2.2 机器列表显示优化
- 在机器列表项中增加了折扣率信息的显示
- 用户可以直观地看到每台机器的折扣率设置

### 3. API接口确认

后端API接口已经支持相关字段：
- `/api/v1/machines/`端点支持discount_rate字段的读取和更新
- 层级数据接口`/api/v1/hierarchical/machine-types`正确返回包含discount_rate的机器信息

## 验证结果

### 数据库验证
1. ✅ Machine表包含discount_rate字段
2. ✅ discount_rate字段类型为Float，默认值为1.0
3. ✅ 已移除不必要的Configuration表及相关外键关系

### API验证
1. ✅ GET /api/v1/machines/ 正常返回机器数据，包含discount_rate字段
2. ✅ POST /api/v1/machines/ 支持discount_rate字段的创建
3. ✅ PUT /api/v1/machines/{id} 支持discount_rate字段的更新
4. ✅ GET /api/v1/hierarchical/machine-types 正常返回完整的层级数据

### 前端验证
1. ✅ 机器列表正确显示discount_rate信息
2. ✅ 机器添加/编辑模态框包含discount_rate输入字段
3. ✅ discount_rate字段输入有合理的验证规则
4. ✅ 表单提交能正确保存discount_rate数据

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

### 数据库模型变更
```python
class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    base_hourly_rate = Column(Float, default=0.0)
    active = Column(Boolean, default=True)
    manufacturer = Column(String)
    discount_rate = Column(Float, default=1.0)  # 固定折扣率字段
    exchange_rate = Column(Float, default=1.0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="machines")
    card_configs = relationship("CardConfig", back_populates="machine", cascade="all, delete-orphan")
```

## 总结

通过本次调整，我们成功实现了用户的需求：
1. 在设备型号中正确定义和显示"固定折扣率"字段
2. 简化了配置结构，将所有配置信息集中到板卡配置中
3. 保持了系统的完整功能和良好的用户体验

现在系统更加符合实际业务需求，用户可以在设备型号层面设置统一的折扣率，同时通过板卡配置管理具体的配置信息。