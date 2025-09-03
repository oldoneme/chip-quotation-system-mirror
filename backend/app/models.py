from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table, DateTime, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import json
import hashlib
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
    quote_unit = Column(String, default="昆山芯信安")  # 报价单位
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
    status = Column(String, default="draft", index=True)  # 状态: draft, pending, approved, rejected, returned, forwarded
    version = Column(String, default="V1.0")  # 版本号
    
    # 审批相关
    approval_status = Column(String, default="not_submitted", index=True)  # 审批状态: not_submitted, pending, approved, rejected, approved_with_changes, returned_for_revision, forwarded, input_requested
    current_approver_id = Column(Integer, ForeignKey("users.id"))  # 当前审批人
    submitted_at = Column(DateTime)  # 提交审批时间
    approved_at = Column(DateTime)  # 审批通过时间
    approved_by = Column(Integer, ForeignKey("users.id"))  # 最终审批人
    rejection_reason = Column(Text)  # 拒绝原因
    wecom_approval_id = Column(String, unique=True)  # 企业微信审批单ID
    wecom_approval_template_id = Column(String)  # 企业微信审批模板ID
    approval_link_token = Column(String, unique=True)  # 审批链接Token
    
    # 系统字段
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = relationship("User", foreign_keys=[created_by])
    approver = relationship("User", foreign_keys=[approved_by])
    current_approver = relationship("User", foreign_keys=[current_approver_id])
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
    action = Column(String, index=True)  # 操作: approve, reject, approve_with_changes, return_for_revision, forward, request_input, submit, withdraw
    status = Column(String, index=True)  # 状态: pending, completed, cancelled
    approver_id = Column(Integer, ForeignKey("users.id"))  # 审批人
    comments = Column(Text)  # 审批意见
    
    # 审批步骤信息
    step_order = Column(Integer, default=1)  # 审批步骤顺序
    is_final_step = Column(Boolean, default=True)  # 是否最终步骤
    
    # 修改相关（针对 approve_with_changes 和 return_for_revision）
    modified_data = Column(Text)  # 修改的数据（JSON格式）
    original_data = Column(Text)  # 原始数据（JSON格式）
    change_summary = Column(Text)  # 修改摘要
    
    # 转交相关（针对 forward）
    forwarded_to_id = Column(Integer, ForeignKey("users.id"))  # 转交给的用户
    forward_reason = Column(Text)  # 转交原因
    
    # 征求意见相关（针对 request_input）
    input_deadline = Column(DateTime)  # 输入截止时间
    input_received = Column(Boolean, default=False)  # 是否已收到输入
    
    # 企业微信审批相关
    wecom_approval_id = Column(String)  # 企业微信审批单ID
    wecom_sp_no = Column(String)  # 企业微信审批编号
    wecom_callback_data = Column(Text)  # 企业微信回调数据（JSON格式）
    
    # 幂等性支持
    event_time = Column(DateTime)  # 事件时间（用于幂等性检查）
    processed = Column(Boolean, default=False)  # 是否已处理
    callback_signature = Column(String)  # 回调签名（用于去重）
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime)  # 处理时间
    deadline = Column(DateTime)  # 审批截止时间
    
    # Relationships
    quote = relationship("Quote", back_populates="approval_records")
    approver = relationship("User", foreign_keys=[approver_id])
    forwarded_to = relationship("User", foreign_keys=[forwarded_to_id])


class QuoteSnapshot(Base):
    """报价快照表 - 提交审批时的数据冻结"""
    __tablename__ = "quote_snapshots"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    data = Column(Text, nullable=False)  # JSON格式的快照数据
    hash = Column(String(64), nullable=False)  # SHA256哈希
    template_id = Column(String, nullable=False)  # 使用的审批模板ID
    approvers = Column(Text)  # JSON格式的审批人列表
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quote = relationship("Quote")
    creator = relationship("User")
    
    def calc_hash(self) -> str:
        """计算数据哈希"""
        # 确保JSON序列化的稳定性
        data_str = json.dumps(json.loads(self.data), sort_keys=True, separators=(',', ':'))
        return hashlib.sha256(data_str.encode('utf-8')).hexdigest()
    
    @classmethod
    def from_quote(cls, quote, template_id: str, approvers: list, creator_id: int = None):
        """从Quote对象创建快照"""
        # 序列化Quote数据
        data = {
            "id": quote.id,
            "quote_number": quote.quote_number,
            "title": quote.title,
            "quote_type": quote.quote_type,
            "customer_name": quote.customer_name,
            "customer_contact": quote.customer_contact,
            "customer_phone": quote.customer_phone,
            "customer_email": quote.customer_email,
            "total_amount": quote.total_amount,
            "currency": quote.currency,
            "description": quote.description,
            "items": [
                {
                    "item_name": item.item_name,
                    "quantity": item.quantity,
                    "unit_price": item.unit_price,
                    "total_price": item.total_price
                }
                for item in quote.items
            ]
        }
        
        data_json = json.dumps(data, sort_keys=True, separators=(',', ':'))
        snapshot = cls(
            quote_id=quote.id,
            data=data_json,
            template_id=template_id,
            approvers=json.dumps(approvers),
            created_by=creator_id
        )
        snapshot.hash = snapshot.calc_hash()
        return snapshot


class EffectiveQuote(Base):
    """生效报价单表 - 审批通过后的正式版本"""
    __tablename__ = "effective_quotes"
    
    id = Column(Integer, primary_key=True, index=True)
    quote_id = Column(Integer, ForeignKey("quotes.id"), nullable=False)
    snapshot_id = Column(Integer, ForeignKey("quote_snapshots.id"), nullable=False)
    version = Column(String, nullable=False, default="1.0")  # 版本号
    
    # 导出文件信息
    export_file_url = Column(String)  # 导出文件URL
    export_file_type = Column(String)  # 文件类型: pdf, excel
    export_checksum = Column(String)  # 文件校验和
    
    # 生效信息
    effective_at = Column(DateTime, default=datetime.utcnow)  # 生效时间
    expires_at = Column(DateTime)  # 过期时间
    created_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    quote = relationship("Quote")
    snapshot = relationship("QuoteSnapshot")
    creator = relationship("User")
    
    @property
    def version_number(self) -> float:
        """获取数值版本号用于比较"""
        try:
            return float(self.version)
        except (ValueError, TypeError):
            return 1.0
    
    @classmethod
    def create_next_version(cls, quote_id: int, snapshot_id: int, creator_id: int = None):
        """创建下一个版本的生效报价单"""
        from sqlalchemy.orm import Session
        # 这里需要注入session，实际使用时在service层处理
        # 获取当前最新版本
        # latest = session.query(cls).filter(cls.quote_id == quote_id).order_by(cls.version_number.desc()).first()
        # next_version = str(latest.version_number + 0.1) if latest else "1.0"
        
        # 暂时使用简单递增
        next_version = "1.0"  # 实际实现中需要查询数据库
        
        return cls(
            quote_id=quote_id,
            snapshot_id=snapshot_id,
            version=next_version,
            created_by=creator_id
        )


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
