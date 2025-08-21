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

class Quotation(Base):
    __tablename__ = "quotations"
    
    id = Column(Integer, primary_key=True, index=True)
    total = Column(Float)
    machine_id = Column(Integer, ForeignKey("machines.id"))
    test_hours = Column(Float, default=1.0)
    created_at = Column(DateTime, default=datetime.utcnow)
    details = Column(String)  # JSON string for detailed breakdown
    
    # Relationships
    machine = relationship("Machine")


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
