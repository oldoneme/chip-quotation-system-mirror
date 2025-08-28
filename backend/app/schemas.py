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


# 新报价单系统 schemas
class QuoteItemBase(BaseModel):
    """报价明细项基本模型"""
    item_name: str = Field(..., description="项目名称")
    item_description: Optional[str] = Field(None, description="项目描述")
    machine_type: Optional[str] = Field(None, description="设备类型")
    supplier: Optional[str] = Field(None, description="供应商")
    machine_model: Optional[str] = Field(None, description="设备型号")
    configuration: Optional[str] = Field(None, description="配置")
    quantity: float = Field(1.0, ge=0, description="数量")
    unit: str = Field("小时", description="单位")
    unit_price: float = Field(0.0, ge=0, description="单价")
    total_price: float = Field(0.0, ge=0, description="小计")
    machine_id: Optional[int] = Field(None, description="设备ID")
    configuration_id: Optional[int] = Field(None, description="配置ID")


class QuoteItemCreate(QuoteItemBase):
    """创建报价明细项"""
    pass


class QuoteItemUpdate(QuoteItemBase):
    """更新报价明细项"""
    item_name: Optional[str] = None
    quantity: Optional[float] = Field(None, ge=0)
    unit_price: Optional[float] = Field(None, ge=0)
    total_price: Optional[float] = Field(None, ge=0)


class QuoteItem(QuoteItemBase):
    """报价明细项返回模型"""
    id: int
    quote_id: int
    
    class Config:
        from_attributes = True


class QuoteBase(BaseModel):
    """报价单基本模型"""
    title: str = Field(..., description="报价标题")
    quote_type: str = Field(..., description="报价类型")
    customer_name: str = Field(..., description="客户名称")
    customer_contact: Optional[str] = Field(None, description="联系人")
    customer_phone: Optional[str] = Field(None, description="联系电话")
    customer_email: Optional[str] = Field(None, description="邮箱")
    customer_address: Optional[str] = Field(None, description="地址")
    currency: str = Field("CNY", description="币种")
    subtotal: float = Field(0.0, ge=0, description="小计")
    discount: float = Field(0.0, ge=0, description="折扣金额")
    tax_rate: float = Field(0.13, ge=0, le=1, description="税率")
    tax_amount: float = Field(0.0, ge=0, description="税额")
    total_amount: float = Field(0.0, ge=0, description="总金额")
    valid_until: Optional[datetime] = Field(None, description="有效期")
    payment_terms: Optional[str] = Field(None, description="付款条件")
    description: Optional[str] = Field(None, description="报价说明")
    notes: Optional[str] = Field(None, description="备注")
    version: str = Field("V1.0", description="版本号")


class QuoteCreate(QuoteBase):
    """创建报价单"""
    items: List[QuoteItemCreate] = Field([], description="报价明细项")


class QuoteUpdate(BaseModel):
    """更新报价单"""
    title: Optional[str] = None
    quote_type: Optional[str] = None
    customer_name: Optional[str] = None
    customer_contact: Optional[str] = None
    customer_phone: Optional[str] = None
    customer_email: Optional[str] = None
    customer_address: Optional[str] = None
    currency: Optional[str] = None
    subtotal: Optional[float] = Field(None, ge=0)
    discount: Optional[float] = Field(None, ge=0)
    tax_rate: Optional[float] = Field(None, ge=0, le=1)
    tax_amount: Optional[float] = Field(None, ge=0)
    total_amount: Optional[float] = Field(None, ge=0)
    valid_until: Optional[datetime] = None
    payment_terms: Optional[str] = None
    description: Optional[str] = None
    notes: Optional[str] = None
    version: Optional[str] = None
    items: Optional[List[QuoteItemUpdate]] = None


class Quote(QuoteBase):
    """报价单返回模型"""
    id: int
    quote_number: str
    status: str
    submitted_at: Optional[datetime] = None
    approved_at: Optional[datetime] = None
    approved_by: Optional[int] = None
    rejection_reason: Optional[str] = None
    wecom_approval_id: Optional[str] = None
    created_by: int
    created_at: datetime
    updated_at: datetime
    items: List[QuoteItem] = []
    
    class Config:
        from_attributes = True


class QuoteList(BaseModel):
    """报价单列表项模型"""
    id: int
    quote_number: str
    title: str
    quote_type: str
    customer_name: str
    currency: str
    total_amount: float
    status: str
    version: str
    created_by: int
    created_at: datetime
    updated_at: datetime
    valid_until: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class QuoteStatusUpdate(BaseModel):
    """报价单状态更新"""
    status: str = Field(..., description="新状态: draft, pending, approved, rejected")
    comments: Optional[str] = Field(None, description="状态更新说明")


class ApprovalRecordBase(BaseModel):
    """审批记录基本模型"""
    action: str = Field(..., description="操作")
    status: str = Field(..., description="状态")
    comments: Optional[str] = Field(None, description="审批意见")


class ApprovalRecordCreate(ApprovalRecordBase):
    """创建审批记录"""
    pass


class ApprovalRecord(ApprovalRecordBase):
    """审批记录返回模型"""
    id: int
    quote_id: int
    approver_id: Optional[int] = None
    wecom_approval_id: Optional[str] = None
    wecom_sp_no: Optional[str] = None
    created_at: datetime
    processed_at: Optional[datetime] = None
    
    class Config:
        from_attributes = True


class QuoteStatistics(BaseModel):
    """报价单统计模型"""
    total: int = 0
    draft: int = 0
    pending: int = 0
    approved: int = 0
    rejected: int = 0
    

class QuoteFilter(BaseModel):
    """报价单筛选参数"""
    status: Optional[str] = None
    quote_type: Optional[str] = None
    customer_name: Optional[str] = None
    created_by: Optional[int] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
