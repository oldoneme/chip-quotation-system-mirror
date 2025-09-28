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
    """级联删除机器类型及其所有关联数据"""
    db_machine_type = db.query(models.MachineType).filter(models.MachineType.id == machine_type_id).first()
    if db_machine_type:
        # 1. 获取该机器类型下的所有供应商
        suppliers = db.query(models.Supplier).filter(models.Supplier.machine_type_id == machine_type_id).all()
        
        for supplier in suppliers:
            # 2. 对每个供应商执行级联删除
            delete_supplier(db, supplier.id)
        
        # 3. 删除机器类型本身
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
    """级联删除供应商及其所有关联数据"""
    db_supplier = db.query(models.Supplier).filter(models.Supplier.id == supplier_id).first()
    if db_supplier:
        # 1. 获取该供应商下的所有机器
        machines = db.query(models.Machine).filter(models.Machine.supplier_id == supplier_id).all()
        
        for machine in machines:
            # 2. 对每台机器执行级联删除
            delete_machine(db, machine.id)
        
        # 3. 删除供应商本身
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
    """级联删除机器及其所有关联数据"""
    db_machine = db.query(models.Machine).filter(models.Machine.id == machine_id).first()
    if db_machine:
        # 1. 删除该机器下的所有板卡配置
        db.query(models.CardConfig).filter(models.CardConfig.machine_id == machine_id).delete()
        
        # 2. 在删除前获取相关信息，避免懒加载错误
        machine_data = schemas.Machine.from_orm(db_machine)
        
        # 3. 删除机器本身
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
    from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

    machine = db.query(models.Machine).filter(models.Machine.id == quotation_request.machine_id).first()
    if not machine:
        raise ValueError("Machine not found")

    def to_decimal(value, field_name: str) -> Decimal:
        if value is None:
            value = 0
        try:
            return Decimal(str(value))
        except (InvalidOperation, TypeError):
            raise ValueError(f"Invalid numeric value for {field_name}: {value}")

    details = quotation_request.details or {}

    base_rate = to_decimal(machine.base_hourly_rate or 0, "base_hourly_rate")
    discount_rate = to_decimal(machine.discount_rate or 1, "discount_rate")
    hourly_total = base_rate * discount_rate

    selected_config_ids = set(details.get('configuration_ids', []) or [])
    include_all_configs = not selected_config_ids
    for config in machine.configurations:
        if include_all_configs or config.id in selected_config_ids:
            hourly_total += to_decimal(config.additional_rate or 0, f"configuration[{config.id}].additional_rate")

    selected_card_ids = set(details.get('card_config_ids', []) or [])
    include_all_cards = not selected_card_ids
    exchange_default = to_decimal(machine.exchange_rate or 1, "exchange_rate")
    machine_currency = (machine.currency or 'RMB').upper()

    for card in machine.card_configs:
        if include_all_cards or card.id in selected_card_ids:
            card_price = to_decimal(card.unit_price or 0, f"card[{card.id}].unit_price")
            card_currency = (card.currency or machine_currency).upper()
            if card_currency == 'USD':
                card_rate = to_decimal(card.exchange_rate or exchange_default, f"card[{card.id}].exchange_rate")
                card_price *= card_rate
            hourly_total += card_price

    for extra in details.get('auxiliary_rates', []) or []:
        hourly_total += to_decimal(extra, "auxiliary_rate")

    hourly_total += to_decimal(details.get('extra_flat_fee') or 0, "extra_flat_fee")

    if machine_currency == 'USD':
        exchange_override = details.get('exchange_rate_override') or details.get('exchange_rate')
        hourly_total *= to_decimal(exchange_override or exchange_default, "exchange_rate_override")

    test_hours = to_decimal(quotation_request.test_hours or 0, "test_hours")
    if test_hours < 0:
        raise ValueError("Test hours cannot be negative")

    total = (hourly_total * test_hours).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(total)

# Enhanced Quotation CRUD operations with permission management
def create_quotation(db: Session, quotation: dict, user_id: int):
    """创建报价（带用户关联）"""
    quotation['created_by'] = user_id
    db_quotation = models.Quotation(**quotation)
    db.add(db_quotation)
    db.commit()
    db.refresh(db_quotation)
    return db_quotation

def get_user_quotations(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    """获取用户的报价列表"""
    return db.query(models.Quotation).filter(
        models.Quotation.created_by == user_id
    ).offset(skip).limit(limit).all()

def update_quotation_status(db: Session, quotation_id: int, status: str, reviewer_id: int, review_comment: str = None):
    """更新报价状态（审核）"""
    db_quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if db_quotation:
        db_quotation.status = status
        db_quotation.reviewed_by = reviewer_id
        db_quotation.review_comment = review_comment
        db_quotation.reviewed_at = models.datetime.utcnow()
        db.commit()
        db.refresh(db_quotation)
    return db_quotation

def update_quotation_priority(db: Session, quotation_id: int, priority: str):
    """更新报价优先级"""
    db_quotation = db.query(models.Quotation).filter(models.Quotation.id == quotation_id).first()
    if db_quotation:
        db_quotation.priority = priority
        db.commit()
        db.refresh(db_quotation)
    return db_quotation

def get_quotations_for_export(db: Session, start_date: str = None, end_date: str = None):
    """获取导出用的报价数据"""
    query = db.query(models.Quotation)
    
    if start_date:
        query = query.filter(models.Quotation.created_at >= start_date)
    if end_date:
        query = query.filter(models.Quotation.created_at <= end_date)
    
    return query.all()

# User CRUD operations
def get_user(db: Session, user_id: int):
    """根据ID获取用户"""
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_userid(db: Session, userid: str):
    """根据企业微信userid获取用户"""
    return db.query(models.User).filter(models.User.userid == userid).first()

def get_users(db: Session, skip: int = 0, limit: int = 100):
    """获取用户列表"""
    return db.query(models.User).offset(skip).limit(limit).all()

def create_user(db: Session, user: schemas.UserCreate):
    """创建用户"""
    db_user = models.User(**user.dict())
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

def update_user(db: Session, user_id: int, update_data: dict):
    """更新用户信息"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        for key, value in update_data.items():
            if hasattr(db_user, key):
                setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
    return db_user

def update_user_profile(db: Session, user_id: int, update_data: dict):
    """更新用户个人资料"""
    return update_user(db, user_id, update_data)

def update_user_status(db: Session, user_id: int, is_active: bool):
    """更新用户状态"""
    db_user = db.query(models.User).filter(models.User.id == user_id).first()
    if db_user:
        db_user.is_active = is_active
        db.commit()
        db.refresh(db_user)
    return db_user

# Operation Log CRUD operations
def log_operation(db: Session, user_id: int, operation: str, details: str = None):
    """记录操作日志"""
    from datetime import datetime
    db_log = models.OperationLog(
        user_id=user_id,
        operation=operation,
        details=details,
        created_at=datetime.utcnow()
    )
    db.add(db_log)
    db.commit()
    db.refresh(db_log)
    return db_log

def get_operation_logs(db: Session, skip: int = 0, limit: int = 100, user_id: int = None):
    """获取操作日志列表"""
    query = db.query(models.OperationLog)
    if user_id:
        query = query.filter(models.OperationLog.user_id == user_id)
    return query.order_by(models.OperationLog.created_at.desc()).offset(skip).limit(limit).all()
