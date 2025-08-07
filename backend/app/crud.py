from sqlalchemy.orm import Session
from sqlalchemy.orm import joinedload
from . import models, schemas

# Machine Type CRUD operations
def get_machine_type(db: Session, machine_type_id: int):
    return db.query(models.MachineType).filter(models.MachineType.id == machine_type_id).first()

def get_machine_type_by_name(db: Session, name: str):
    return db.query(models.MachineType).filter(models.MachineType.name == name).first()

def get_machine_types(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.MachineType).offset(skip).limit(limit).all()

def create_machine_type(db: Session, machine_type: schemas.MachineTypeCreate):
    db_machine_type = models.MachineType(**machine_type.dict())
    db.add(db_machine_type)
    db.commit()
    db.refresh(db_machine_type)
    return db_machine_type

def update_machine_type(db: Session, machine_type_id: int, machine_type: schemas.MachineTypeUpdate):
    db_machine_type = db.query(models.MachineType).filter(models.MachineType.id == machine_type_id).first()
    if db_machine_type:
        update_data = machine_type.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_machine_type, key, value)
        db.commit()
        db.refresh(db_machine_type)
    return db_machine_type

def delete_machine_type(db: Session, machine_type_id: int):
    db_machine_type = db.query(models.MachineType).filter(models.MachineType.id == machine_type_id).first()
    if db_machine_type:
        db.delete(db_machine_type)
        db.commit()
    return db_machine_type

# Supplier CRUD operations
def get_supplier(db: Session, supplier_id: int):
    return db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()

def get_supplier_by_name(db: Session, name: str):
    return db.query(models.Supplier).filter(models.Supplier.name == name).first()

def get_suppliers(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Supplier).offset(skip).limit(limit).all()

def create_supplier(db: Session, supplier: schemas.SupplierCreate):
    db_supplier = models.Supplier(**supplier.dict())
    db.add(db_supplier)
    db.commit()
    db.refresh(db_supplier)
    return db_supplier

def update_supplier(db: Session, supplier_id: int, supplier: schemas.SupplierUpdate):
    db_supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if db_supplier:
        update_data = supplier.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_supplier, key, value)
        db.commit()
        db.refresh(db_supplier)
    return db_supplier

def delete_supplier(db: Session, supplier_id: int):
    db_supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if db_supplier:
        db.delete(db_supplier)
        db.commit()
    return db_supplier

# Machine CRUD operations
def get_machine(db: Session, machine_id: int):
    return db.query(models.Machine).filter(models.Machine.id == machine_id).first()

def get_machines(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Machine).offset(skip).limit(limit).all()

def create_machine(db: Session, machine: schemas.MachineCreate):
    db_machine = models.Machine(**machine.dict())
    db.add(db_machine)
    db.commit()
    db.refresh(db_machine)
    return db_machine

def update_machine(db: Session, machine_id: int, machine: schemas.MachineUpdate):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if db_machine:
        update_data = machine.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_machine, key, value)
        db.commit()
        db.refresh(db_machine)
    return db_machine

def delete_machine(db: Session, machine_id: int):
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if db_machine:
        # 在删除前获取相关信息，避免懒加载错误
        machine_data = schemas.Machine.from_orm(db_machine)
        db.delete(db_machine)
        db.commit()
        return machine_data
    return None

# Configuration CRUD operations
def get_configuration(db: Session, configuration_id: int):
    return db.query(models.Configuration).filter(models.Configuration.id == configuration_id).first()

def get_configurations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Configuration).offset(skip).limit(limit).all()

def create_configuration(db: Session, configuration: schemas.ConfigurationCreate):
    db_configuration = models.Configuration(**configuration.dict())
    db.add(db_configuration)
    db.commit()
    db.refresh(db_configuration)
    return db_configuration

def update_configuration(db: Session, configuration_id: int, configuration: schemas.ConfigurationUpdate):
    db_configuration = db.query(models.Configuration).filter(models.Configuration.id == configuration_id).first()
    if db_configuration:
        update_data = configuration.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_configuration, key, value)
        db.commit()
        db.refresh(db_configuration)
    return db_configuration

def delete_configuration(db: Session, configuration_id: int):
    db_configuration = db.query(models.Configuration).filter(models.Configuration.id == configuration_id).first()
    if db_configuration:
        db.delete(db_configuration)
        db.commit()
    return db_configuration

# Card Config CRUD operations
def get_card_config(db: Session, card_config_id: int):
    return db.query(models.CardConfig).filter(models.CardConfig.id == card_config_id).first()

def get_card_configs(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.CardConfig).offset(skip).limit(limit).all()

def create_card_config(db: Session, card_config: schemas.CardConfigCreate):
    db_card_config = models.CardConfig(**card_config.dict())
    db.add(db_card_config)
    db.commit()
    db.refresh(db_card_config)
    return db_card_config

def update_card_config(db: Session, card_config_id: int, card_config: schemas.CardConfigUpdate):
    db_card_config = db.query(models.CardConfig).filter(models.CardConfig.id == card_config_id).first()
    if db_card_config:
        update_data = card_config.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_card_config, key, value)
        db.commit()
        db.refresh(db_card_config)
    return db_card_config

def delete_card_config(db: Session, card_config_id: int):
    db_card_config = db.query(models.CardConfig).filter(models.CardConfig.id == card_config_id).first()
    if db_card_config:
        db.delete(db_card_config)
        db.commit()
    return db_card_config

# Auxiliary Equipment CRUD operations
def get_auxiliary_equipment(db: Session, equipment_id: int):
    return db.query(models.AuxiliaryEquipment).filter(models.AuxiliaryEquipment.id == equipment_id).first()

def get_auxiliary_equipments(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.AuxiliaryEquipment).offset(skip).limit(limit).all()

def create_auxiliary_equipment(db: Session, equipment: schemas.AuxiliaryEquipmentCreate):
    db_equipment = models.AuxiliaryEquipment(**equipment.dict())
    db.add(db_equipment)
    db.commit()
    db.refresh(db_equipment)
    return db_equipment

def update_auxiliary_equipment(db: Session, equipment_id: int, equipment: schemas.AuxiliaryEquipmentUpdate):
    db_equipment = db.query(models.AuxiliaryEquipment).filter(models.AuxiliaryEquipment.id == equipment_id).first()
    if db_equipment:
        update_data = equipment.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_equipment, key, value)
        db.commit()
        db.refresh(db_equipment)
    return db_equipment

def delete_auxiliary_equipment(db: Session, equipment_id: int):
    db_equipment = db.query(models.AuxiliaryEquipment).filter(models.AuxiliaryEquipment.id == equipment_id).first()
    if db_equipment:
        db.delete(db_equipment)
        db.commit()
    return db_equipment

# Quotation CRUD operations
def get_quotation(db: Session, quotation_id: int):
    return db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()

def get_quotations(db: Session, skip: int = 0, limit: int = 100):
    return db.query(models.Quotation).offset(skip).limit(limit).all()

def create_quotation(db: Session, quotation: schemas.QuotationCreate):
    db_quotation = models.Quotation(**quotation.dict())
    db.add(db_quotation)
    db.commit()
    db.refresh(db_quotation)
    return db_quotation

def update_quotation(db: Session, quotation_id: int, quotation: schemas.QuotationUpdate):
    db_quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if db_quotation:
        update_data = quotation.dict(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_quotation, key, value)
        db.commit()
        db.refresh(db_quotation)
    return db_quotation

def delete_quotation(db: Session, quotation_id: int):
    db_quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if db_quotation:
        db.delete(db_quotation)
        db.commit()
    return db_quotation

def calculate_quotation(db: Session, quotation_request: schemas.QuotationRequest):
    # Get the machine
    machine = db.query(models.Machine).filter(models.Machine.id == quotation_request.machine_id).first()
    if not machine:
        raise ValueError("Machine not found")
    
    # Calculate total: base hourly rate + configuration additional rate
    total = machine.base_hourly_rate if machine.base_hourly_rate else 0.0
    
    # Add configuration additional rates
    for config in machine.configurations:
        total += config.additional_rate if config.additional_rate else 0.0
    
    # Multiply by test hours
    total *= quotation_request.test_hours
    
    return total