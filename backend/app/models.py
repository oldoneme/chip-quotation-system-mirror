from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
from .database import Base

class MachineType(Base):
    __tablename__ = "machine_types"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    
    # Relationships
    suppliers = relationship("Supplier", back_populates="machine_type")

class Supplier(Base):
    __tablename__ = "suppliers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    machine_type_id = Column(Integer, ForeignKey("machine_types.id"))
    
    # Relationships
    machine_type = relationship("MachineType", back_populates="suppliers")
    machines = relationship("Machine", back_populates="supplier")

class Machine(Base):
    __tablename__ = "machines"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    active = Column(Boolean, default=True)
    manufacturer = Column(String)
    base_hourly_rate = Column(Float, default=0.0)  # 基础小时费率
    discount_rate = Column(Float, default=1.0)
    exchange_rate = Column(Float, default=1.0)
    currency = Column(String, default="RMB")  # 币种: RMB 或 USD
    supplier_id = Column(Integer, ForeignKey("suppliers.id"))
    
    # Relationships
    supplier = relationship("Supplier", back_populates="machines")
    configurations = relationship("Configuration", back_populates="machine", cascade="all, delete-orphan")
    card_configs = relationship("CardConfig", back_populates="machine", cascade="all, delete-orphan")

class Configuration(Base):
    __tablename__ = "configurations"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    description = Column(String)
    additional_rate = Column(Float, default=0.0)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    
    # Relationships
    machine = relationship("Machine", back_populates="configurations")

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

class AuxiliaryEquipment(Base):
    __tablename__ = "auxiliary_equipment"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    description = Column(String)
    hourly_rate = Column(Float)
    type = Column(String)  # 新增字段，用于区分handler和prober

# 移除Personnel模型，改为使用标准值

# 报价单相关模型
class Quote(Base):
    """报价单主表"""
    __tablename__ = "quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_number = Column(String, unique=True, index=True)  # 报价单号 QT202408001
    title = Column(String, index=True)  # 报价标题
    quote_type = Column(String, index=True)  # 报价类型: inquiry, tooling, engineering, mass_production, process, comprehensive
    
    # 客户信息
    customer_name = Column(String, index=True)  # 客户名称
    customer_contact = Column(String)  # 联系人
    customer_phone = Column(String)  # 联系电话
    customer_email = Column(String)  # 邮箱
    customer_address = Column(Text)  # 地址
    
    # 报价信息
    currency = Column(String, default="CNY")  # 币种 CNY/USD
    subtotal = Column(Float, default=0.0)  # 小计
    discount = Column(Float, default=0.0)  # 折扣金额
    tax_rate = Column(Float, default=0.13)  # 税率
    tax_amount = Column(Float, default=0.0)  # 税额
    total_amount = Column(Float, default=0.0)  # 总金额
    
    # 条件信息
    valid_until = Column(DateTime)  # 有效期
    payment_terms = Column(String)  # 付款条件
    description = Column(Text)  # 报价说明
    notes = Column(Text)  # 备注
    
    # 状态管理
    status = Column(String, default="draft", index=True)  # 状态: draft, pending, approved, rejected
    version = Column(String, default="V1.0")  # 版本号
    
    # 审批相关
    submitted_at = Column(DateTime)  # 提交审批时间
    approved_at = Column(DateTime)  # 审批通过时间
    approved_by = Column(Integer, ForeignKey("users.id"))  # 审批人
    rejection_reason = Column(Text)  # 拒绝原因
    wecom_approval_id = Column(String)  # 企业微信审批单ID
    
    # 系统字段
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    items = relationship("QuoteItem", back_populates="quote", cascade="all, delete-orphan")
    approval_records = relationship("ApprovalRecord", back_populates="quote", cascade="all, delete-orphan")


class QuoteItem(Base):
    """报价单明细项目"""
    __tablename__ = "quote_items"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    
    # 项目信息
    item_name = Column(String)  # 项目名称
    item_description = Column(Text)  # 项目描述
    machine_type = Column(String)  # 设备类型
    supplier = Column(String)  # 供应商
    machine_model = Column(String)  # 设备型号
    configuration = Column(String)  # 配置
    
    # 数量和价格
    quantity = Column(Float, default=1.0)  # 数量
    unit = Column(String, default="小时")  # 单位
    unit_price = Column(Float, default=0.0)  # 单价
    total_price = Column(Float, default=0.0)  # 小计
    
    # 关联信息
    machine_id = Column(Integer, ForeignKey("machines.id"))
    configuration_id = Column(Integer, ForeignKey("configurations.id"))
    
    # Relationships
    quote = relationship("Quote", back_populates="items")
    machine = relationship("Machine")
    config = relationship("Configuration")


class ApprovalRecord(Base):
    """审批记录表"""
    __tablename__ = "approval_records"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"))
    
    # 审批信息
    action = Column(String)  # 操作: submit, approve, reject, withdraw
    status = Column(String)  # 状态: pending, approved, rejected
    approver_id = Column(Integer, ForeignKey("users.id"))  # 审批人
    comments = Column(Text)  # 审批意见
    
    # 企业微信审批相关
    wecom_approval_id = Column(String)  # 企业微信审批单ID
    wecom_sp_no = Column(String)  # 企业微信审批编号
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)  # 处理时间
    
    # Relationships
    quote = relationship("Quote", back_populates="approval_records")
    approver = relationship("User")


class QuoteTemplate(Base):
    """报价模板表"""
    __tablename__ = "quote_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)  # 模板名称
    quote_type = Column(String)  # 报价类型
    description = Column(Text)  # 模板描述
    template_data = Column(Text)  # 模板数据(JSON格式)
    
    # 系统字段
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    creator = relationship("User")


# 保留原有的简单Quotation表做兼容性处理
class Quotation(Base):
    __tablename__ = "quotations"
    
    id = Column(Integer, primary_key=True, index=True)
    total = Column(Float)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    test_hours = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    details = Column(String)  # JSON string for detailed breakdown
    
    # Permission management fields
    created_by = Column(Integer, ForeignKey("users.id"))  # 创建者
    status = Column(String, default="pending")  # 状态: pending, approved, rejected, completed
    priority = Column(String, default="normal")  # 优先级: low, normal, high, urgent
    reviewed_by = Column(Integer, ForeignKey("users.id"))  # 审核者
    reviewed_at = Column(DateTime)  # 审核时间
    review_comment = Column(Text)  # 审核备注
    
    # Relationships
    machine = relationship("Machine")
    creator = relationship("User", foreign_keys=[created_by])
    reviewer = relationship("User", foreign_keys=[reviewed_by])


# 用户认证相关模型
class User(Base):
    """企业微信用户模型"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    userid = Column(String, unique=True, index=True)  # 企业微信用户ID
    name = Column(String, index=True)  # 用户姓名
    mobile = Column(String)  # 手机号
    email = Column(String)  # 邮箱
    department = Column(String)  # 部门
    position = Column(String)  # 职位
    role = Column(String, default="user")  # 角色: super_admin, admin, manager, user
    is_active = Column(Boolean, default=True)  # 是否激活
    avatar = Column(String)  # 头像URL
    
    # 企业微信相关信息
    department_ids = Column(Text)  # 部门ID列表，JSON格式存储
    is_leader_in_dept = Column(Text)  # 在各部门中是否为主管，JSON格式
    direct_leader = Column(String)  # 直属上级
    
    # 系统字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime)
    
    # Relationships
    sessions = relationship("UserSession", back_populates="user", cascade="all, delete-orphan")


class UserSession(Base):
    """用户会话模型"""
    __tablename__ = "user_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    session_token = Column(String, unique=True, index=True)  # 会话令牌
    expires_at = Column(DateTime)  # 过期时间
    created_at = Column(DateTime, default=datetime.utcnow)
    user_agent = Column(String)  # 浏览器信息
    ip_address = Column(String)  # IP地址
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Department(Base):
    """部门模型"""
    __tablename__ = "departments"
    
    id = Column(Integer, primary_key=True, index=True)
    dept_id = Column(Integer, unique=True, index=True)  # 企业微信部门ID
    name = Column(String, index=True)  # 部门名称
    parent_id = Column(Integer)  # 上级部门ID
    order = Column(Integer, default=0)  # 排序
    is_allowed = Column(Boolean, default=False)  # 是否允许访问系统
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class OperationLog(Base):
    """操作日志模型"""
    __tablename__ = "operation_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    operation = Column(String, index=True)  # 操作类型
    details = Column(Text)  # 操作详情
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    user = relationship("User")
