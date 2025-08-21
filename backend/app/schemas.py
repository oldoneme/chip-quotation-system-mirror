from pydantic import BaseModel, validator, Field
from typing import List, Optional
from datetime import datetime

# Forward declarations to resolve circular references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Machine

# Machine Type schemas
class MachineTypeBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="机器类型名称")
    description: Optional[str] = Field(None, max_length=500, description="机器类型描述")

class MachineTypeCreate(MachineTypeBase):
    pass

class MachineTypeUpdate(MachineTypeBase):
    name: Optional[str] = None

class MachineType(MachineTypeBase):
    id: int
    
    class Config:
        from_attributes = True

# Supplier schemas
class SupplierBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=100, description="供应商名称")
    machine_type_id: int = Field(..., gt=0, description="机器类型ID")

class SupplierCreate(SupplierBase):
    pass

class SupplierUpdate(SupplierBase):
    name: Optional[str] = None
    machine_type_id: Optional[int] = None

class Supplier(SupplierBase):
    id: int
    machine_type: Optional[MachineType] = None  # 添加machine_type关系
    
    class Config:
        from_attributes = True

# Machine schemas
class MachineBase(BaseModel):
    name: str
    description: Optional[str] = None
    active: Optional[bool] = True
    manufacturer: Optional[str] = None
    base_hourly_rate: Optional[float] = 0.0
    discount_rate: Optional[float] = 1.0
    exchange_rate: Optional[float] = 1.0
    currency: Optional[str] = "RMB"  # 币种: RMB 或 USD
    supplier_id: Optional[int] = None

    @validator('discount_rate')
    def validate_discount_rate(cls, v):
        if v is not None and (v <= 0 or v > 2.0):
            raise ValueError('Discount rate must be between 0 and 2.0')
        return v
    
    @validator('exchange_rate')
    def validate_exchange_rate(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Exchange rate must be positive')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        if v not in ["RMB", "USD"]:
            raise ValueError('Currency must be either RMB or USD')
        return v
    
    @validator('name')
    def validate_name(cls, v):
        if not v or not v.strip():
            raise ValueError('Machine name cannot be empty')
        return v.strip()

class MachineCreate(MachineBase):
    pass

class MachineUpdate(MachineBase):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    manufacturer: Optional[str] = None
    base_hourly_rate: Optional[float] = None
    discount_rate: Optional[float] = None
    exchange_rate: Optional[float] = None
    currency: Optional[str] = None
    supplier_id: Optional[int] = None

class Machine(MachineBase):
    id: int
    supplier: Optional[Supplier] = None  # 使supplier字段可选
    
    class Config:
        from_attributes = True

# Configuration schemas
class ConfigurationBase(BaseModel):
    name: str
    description: Optional[str] = None
    additional_rate: Optional[float] = 0.0
    machine_id: int

class ConfigurationCreate(ConfigurationBase):
    pass

class ConfigurationUpdate(ConfigurationBase):
    name: Optional[str] = None
    additional_rate: Optional[float] = None
    machine_id: Optional[int] = None

class Configuration(ConfigurationBase):
    id: int
    machine_id: int
    
    class Config:
        from_attributes = True

# Card Config schemas (替代原来的Card和CardType)
class CardConfigBase(BaseModel):
    part_number: Optional[str] = None
    board_name: Optional[str] = None
    unit_price: Optional[float] = 0.0
    currency: Optional[str] = "RMB"
    exchange_rate: Optional[float] = 1.0
    machine_id: int

    @validator('unit_price')
    def validate_unit_price(cls, v):
        if v is not None and v < 0:
            raise ValueError('Unit price must be non-negative')
        return v
    
    @validator('exchange_rate')
    def validate_exchange_rate(cls, v):
        if v is not None and v <= 0:
            raise ValueError('Exchange rate must be positive')
        return v
    
    @validator('currency')
    def validate_currency(cls, v):
        if v not in ["RMB", "USD"]:
            raise ValueError('Currency must be either RMB or USD')
        return v

class CardConfigCreate(CardConfigBase):
    pass

class CardConfigUpdate(CardConfigBase):
    part_number: Optional[str] = None
    board_name: Optional[str] = None
    unit_price: Optional[float] = None
    currency: Optional[str] = None
    exchange_rate: Optional[float] = None
    machine_id: Optional[int] = None

class CardConfig(CardConfigBase):
    id: int
    
    class Config:
        from_attributes = True

# Auxiliary Equipment schemas
class AuxiliaryEquipmentBase(BaseModel):
    name: str
    description: Optional[str] = None
    hourly_rate: float
    type: str  # 新增字段，用于区分handler和prober

class AuxiliaryEquipmentCreate(AuxiliaryEquipmentBase):
    pass

class AuxiliaryEquipmentUpdate(AuxiliaryEquipmentBase):
    name: Optional[str] = None
    hourly_rate: Optional[float] = None
    type: Optional[str] = None

class AuxiliaryEquipment(AuxiliaryEquipmentBase):
    id: int
    
    class Config:
        from_attributes = True

# Personnel schemas
class PersonnelBase(BaseModel):
    name: str
    role: str
    hourly_rate: float
    hours_per_day: int = 8
    days_per_week: int = 5
    weeks_per_year: int = 48
    vacation_weeks: int = 4
    sick_weeks: int = 2
    hourly_rate_currency: str = "USD"
    hourly_rate_usd: float

class PersonnelCreate(PersonnelBase):
    pass

class PersonnelUpdate(PersonnelBase):
    name: Optional[str] = None
    role: Optional[str] = None
    hourly_rate: Optional[float] = None

class Personnel(PersonnelBase):
    id: int
    
    class Config:
        from_attributes = True

# Quotation schemas
class QuotationBase(BaseModel):
    total: float
    machine_id: Optional[int] = None
    test_hours: Optional[float] = 1.0
    details: Optional[str] = None

class QuotationCreate(QuotationBase):
    machine_id: int
    test_hours: float = 1.0

class QuotationUpdate(BaseModel):
    total: Optional[float] = None
    machine_id: Optional[int] = None
    test_hours: Optional[float] = None
    details: Optional[str] = None

class Quotation(QuotationBase):
    id: int
    created_at: Optional[str] = None
    
    class Config:
        from_attributes = True

# Request/Response schemas for API
class QuotationRequest(BaseModel):
    machine_id: int
    test_hours: float = 1.0
    details: Optional[dict] = None

class QuotationResponse(BaseModel):
    total: float
    machine_id: Optional[int] = None
    test_hours: Optional[float] = None
    details: Optional[dict] = None

# User schemas
class UserBase(BaseModel):
    userid: str = Field(..., min_length=1, max_length=64, description="企业微信用户ID")
    name: str = Field(..., min_length=1, max_length=100, description="用户姓名")
    mobile: Optional[str] = Field(None, max_length=20, description="手机号")
    email: Optional[str] = Field(None, max_length=100, description="邮箱")
    department: Optional[str] = Field(None, max_length=100, description="部门")
    position: Optional[str] = Field(None, max_length=100, description="职位")
    role: str = Field(default="user", description="角色: super_admin, admin, manager, user")
    is_active: bool = Field(default=True, description="是否激活")
    avatar: Optional[str] = Field(None, description="头像URL")

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
    avatar: Optional[str] = None

class User(UserBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    last_login: Optional[datetime] = None
    
    class Config:
        from_attributes = True


# 新增的报价权限管理相关schemas
class QuotationStatusUpdate(BaseModel):
    status: str = Field(..., description="报价状态: pending, approved, rejected, completed")
    comment: Optional[str] = Field(None, max_length=500, description="审核备注")
    
    @validator('status')
    def validate_status(cls, v):
        allowed_statuses = ['pending', 'approved', 'rejected', 'completed']
        if v not in allowed_statuses:
            raise ValueError(f'状态必须是以下之一: {allowed_statuses}')
        return v


class QuotationPriorityUpdate(BaseModel):
    priority: str = Field(..., description="优先级: low, normal, high, urgent")
    
    @validator('priority')
    def validate_priority(cls, v):
        allowed_priorities = ['low', 'normal', 'high', 'urgent']
        if v not in allowed_priorities:
            raise ValueError(f'优先级必须是以下之一: {allowed_priorities}')
        return v


# 操作日志相关schemas
class OperationLogBase(BaseModel):
    user_id: int
    operation: str = Field(..., description="操作类型")
    details: Optional[str] = Field(None, description="操作详情")
    created_at: Optional[datetime] = None


class OperationLog(OperationLogBase):
    id: int
    user_name: Optional[str] = None
    
    class Config:
        from_attributes = True


# 用户信息管理相关schemas
class UserProfileUpdate(BaseModel):
    """用户个人信息更新"""
    mobile: Optional[str] = Field(None, max_length=20)
    email: Optional[str] = Field(None, max_length=100)
    
    @validator('mobile')
    def validate_mobile(cls, v):
        if v and len(v) < 11:
            raise ValueError('手机号长度不能少于11位')
        return v


class UserManagementUpdate(BaseModel):
    """管理员用户管理更新"""
    name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    department: Optional[str] = None
    position: Optional[str] = None
    is_active: Optional[bool] = None


# 统计分析相关schemas
class QuotationStats(BaseModel):
    """报价统计信息"""
    total_count: int
    pending_count: int
    approved_count: int
    rejected_count: int
    total_amount: float
    avg_amount: float
    period: str = Field(..., description="统计周期")


class UserStats(BaseModel):
    """用户统计信息"""
    user_id: int
    user_name: str
    quotation_count: int
    approved_count: int
    total_amount: float
    success_rate: float
