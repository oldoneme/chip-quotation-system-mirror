from sqlalchemy import Column, Integer, String, Float, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
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