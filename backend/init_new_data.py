from app.database import SessionLocal
from app import crud, schemas

def init_data():
    db = SessionLocal()
    
    # 创建机器类型
    machine_types_data = [
        {"name": "测试机", "description": "芯片测试设备"},
        {"name": "分选机", "description": "芯片分选设备"},
        {"name": "探针台", "description": "晶圆测试设备"}
    ]
    
    machine_types = []
    for mt_data in machine_types_data:
        # 检查是否已存在
        existing_mt = crud.get_machine_type_by_name(db, name=mt_data["name"])
        if not existing_mt:
            mt_create = schemas.MachineTypeCreate(**mt_data)
            machine_type = crud.create_machine_type(db, mt_create)
            machine_types.append(machine_type)
            print(f"Created machine type: {machine_type.name}")
        else:
            machine_types.append(existing_mt)
            print(f"Machine type already exists: {existing_mt.name}")
    
    # 创建供应商
    suppliers_data = [
        {"name": "Teradyne", "machine_type_id": machine_types[0].id},
        {"name": "Advantest", "machine_type_id": machine_types[0].id},
        {"name": "ASM Pacific", "machine_type_id": machine_types[1].id},
        {"name": "上海微电子", "machine_type_id": machine_types[2].id}
    ]
    
    suppliers = []
    for s_data in suppliers_data:
        # 检查是否已存在
        existing_supplier = crud.get_supplier_by_name(db, name=s_data["name"])
        if not existing_supplier:
            s_create = schemas.SupplierCreate(**s_data)
            supplier = crud.create_supplier(db, s_create)
            suppliers.append(supplier)
            print(f"Created supplier: {supplier.name}")
        else:
            suppliers.append(existing_supplier)
            print(f"Supplier already exists: {existing_supplier.name}")
    
    # 创建机器
    machines_data = [
        {"name": "J750", "description": "Basic IC tester", "base_hourly_rate": 50.0, "supplier_id": suppliers[0].id},
        {"name": "T2000", "description": "High-end SOC tester", "base_hourly_rate": 100.0, "supplier_id": suppliers[1].id},
        {"name": "T800", "description": "Mid-range tester", "base_hourly_rate": 75.0, "supplier_id": suppliers[0].id},
        {"name": "AD825", "description": "High-speed sorter", "base_hourly_rate": 30.0, "supplier_id": suppliers[2].id}
    ]
    
    machines = []
    for m_data in machines_data:
        m_create = schemas.MachineCreate(**m_data)
        machine = crud.create_machine(db, m_create)
        machines.append(machine)
        print(f"Created machine: {machine.name}")
    
    # 创建板卡配置
    card_configs_data = [
        {"part_number": "APU12-001", "board_name": "Digital Board", "unit_price": 1500.0, "machine_id": machines[0].id},
        {"part_number": "APU40-002", "board_name": "High-Performance Digital Board", "unit_price": 3000.0, "machine_id": machines[0].id},
        {"part_number": "HSP40-003", "board_name": "High-Speed Digital Board", "unit_price": 2500.0, "machine_id": machines[1].id},
        {"part_number": "PS1600-004", "board_name": "Power Supply Board", "unit_price": 2000.0, "machine_id": machines[1].id}
    ]
    
    for cc_data in card_configs_data:
        existing_cc = db.query(crud.models.CardConfig).filter(
            crud.models.CardConfig.part_number == cc_data["part_number"],
            crud.models.CardConfig.machine_id == cc_data["machine_id"]
        ).first()
        if not existing_cc:
            cc_create = schemas.CardConfigCreate(**cc_data)
            card_config = crud.create_card_config(db, cc_create)
            print(f"创建板卡配置: {cc_data['part_number']}")
        else:
            print(f"板卡配置已存在: {cc_data['part_number']}")
    
    # 创建辅助设备
    aux_equipments_data = [
        {"name": "F550", "description": "科休F550分选机", "hourly_rate": 200, "type": "handler"},
        {"name": "Handler800", "description": "ASM Pacific Handler800分选机", "hourly_rate": 250, "type": "handler"},
        {"name": "Prober100", "description": "探针台100", "hourly_rate": 300, "type": "prober"},
        {"name": "Prober200", "description": "探针台200", "hourly_rate": 350, "type": "prober"}
    ]
    
    for ae_data in aux_equipments_data:
        # 检查是否已存在
        existing_ae = db.query(crud.models.AuxiliaryEquipment).filter(
            crud.models.AuxiliaryEquipment.name == ae_data["name"]
        ).first()
        if not existing_ae:
            ae_create = schemas.AuxiliaryEquipmentCreate(**ae_data)
            aux_equipment = crud.create_auxiliary_equipment(db, ae_create)
            print(f"创建辅助设备: {ae_data['name']}")
        else:
            print(f"辅助设备已存在: {ae_data['name']}")

    db.close()
    print("数据初始化完成!")

if __name__ == "__main__":
    init_data()