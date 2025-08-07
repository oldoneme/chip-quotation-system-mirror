# 数据库结构调整报告 (第二版)

## 项目概述

根据用户需求，我们对芯片测试报价系统的数据库结构进行了进一步调整。主要变更包括：
1. 在设备型号（Machine）中移除"基础小时费率"（base_hourly_rate）字段
2. 保留设备型号中的"固定折扣率"（discount_rate）字段
3. 所有价格相关配置都定义在对应的板卡配置详情中

## 已完成的调整

### 1. 数据库模型更新

#### 1.1 Machine模型变更
- 从Machine实体中移除了`base_hourly_rate`字段
- 保留了`discount_rate`字段，类型为Float，默认值为1.0
- 更新了相关的schemas定义

#### 1.2 数据库表结构
```python
class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    active = Column(Boolean, default=True)
    manufacturer = Column(String)
    discount_rate = Column(Float, default=1.0)  # 固定折扣率字段（保留）
    exchange_rate = Column(Float, default=1.0)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="machines")
    card_configs = relationship("CardConfig", back_populates="machine", cascade="all, delete-orphan")
```

### 2. API接口更新

#### 2.1 Machine Schemas更新
- 从MachineBase、MachineCreate和MachineUpdate schemas中移除了base_hourly_rate字段
- 保留了discount_rate字段

### 3. 前端界面更新

#### 3.1 机器列表显示优化
- 从机器列表项中移除了基础小时费率的显示
- 保留了折扣率信息的显示

#### 3.2 机器模态框更新
- 从机器添加/编辑模态框中移除了基础小时费率输入项
- 保留了固定折扣率字段输入项

## 验证结果

### 数据库验证
1. ✅ Machine表已移除base_hourly_rate字段
2. ✅ Machine表保留discount_rate字段
3. ✅ 相关外键关系保持不变

### API验证
1. ✅ GET /api/v1/machines/ 正常返回机器数据，不包含base_hourly_rate字段
2. ✅ POST /api/v1/machines/ 不再接受base_hourly_rate字段
3. ✅ PUT /api/v1/machines/{id} 不再接受base_hourly_rate字段更新
4. ✅ GET /api/v1/hierarchical/machine-types 正常返回完整的层级数据

### 前端验证
1. ✅ 机器列表不再显示基础小时费率信息
2. ✅ 机器添加/编辑模态框移除了基础小时费率输入字段
3. ✅ 机器添加/编辑模态框保留了固定折扣率输入字段
4. ✅ 表单提交能正确保存折扣率数据

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

### 数据库模型变更详情
```python
# 变更前
class MachineBase(BaseModel):
    name: str
    description: Optional[str] = None
    base_hourly_rate: Optional[float] = 0.0  # 已移除
    active: Optional[bool] = True
    manufacturer: Optional[str] = None
    discount_rate: Optional[float] = 1.0
    exchange_rate: Optional[float] = 1.0
    supplier_id: int

# 变更后
class MachineBase(BaseModel):
    name: str
    description: Optional[str] = None
    active: Optional[bool] = True
    manufacturer: Optional[str] = None
    discount_rate: Optional[float] = 1.0  # 保留
    exchange_rate: Optional[float] = 1.0
    supplier_id: int
```

## 总结

通过本次调整，我们成功实现了用户的最新需求：
1. 在设备型号中移除了"基础小时费率"字段
2. 保留了设备型号中的"固定折扣率"字段
3. 确保所有价格相关配置都定义在对应的板卡配置详情中
4. 保持了系统的完整功能和良好的用户体验

现在系统更加符合实际业务需求，设备型号只包含基本信息和折扣率，具体的价格信息都通过板卡配置来管理。