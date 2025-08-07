from pydantic import BaseModel
from typing import List, Optional

# Forward declarations to resolve circular references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from . import Machine
    from . import Personnel

# Machine Type schemas
class MachineTypeBase(BaseModel):
    name: str
    description: Optional[str] = None

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
    name: str
    machine_type_id: int

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
    discount_rate: Optional[float] = 1.0
    exchange_rate: Optional[float] = 1.0
    currency: Optional[str] = "RMB"  # 币种: RMB 或 USD
    supplier_id: Optional[int] = None

class MachineCreate(MachineBase):
    pass

class MachineUpdate(MachineBase):
    name: Optional[str] = None
    description: Optional[str] = None
    active: Optional[bool] = None
    manufacturer: Optional[str] = None
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
class QuotationRequest(BaseModel):
    machine_id: int
    test_hours: float

class QuotationResponse(BaseModel):
    total: float
    machine_id: int
    test_hours: float

class QuotationBase(BaseModel):
    project_name: str
    description: Optional[str] = None
    total_amount: float

class QuotationCreate(QuotationBase):
    pass

class QuotationUpdate(QuotationBase):
    project_name: Optional[str] = None
    description: Optional[str] = None
    total_amount: Optional[float] = None

class Quotation(QuotationBase):
    id: int
    
    class Config:
        from_attributes = True