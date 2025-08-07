from app.database import SessionLocal
from app import models

def view_database_content():
    session = SessionLocal()
    
    print("=== DATABASE STRUCTURE REPORT ===\n")
    
    # 查看供应商表
    print("1. Suppliers Table:")
    suppliers = session.query(models.Supplier).all()
    if suppliers:
        for supplier in suppliers:
            print(f"   ID: {supplier.id}, Name: {supplier.name}")
    else:
        print("   No suppliers found")
    
    print("\n2. Machines Table:")
    machines = session.query(models.Machine).all()
    if machines:
        for machine in machines:
            print(f"   ID: {machine.id}, Name: {machine.name}, Supplier ID: {machine.supplier_id}")
            # 显示关联的供应商名称
            supplier = session.query(models.Supplier).filter(models.Supplier.id == machine.supplier_id).first()
            if supplier:
                print(f"      -> Supplier: {supplier.name}")
    else:
        print("   No machines found")
    
    print("\n3. Configurations Table:")
    configurations = session.query(models.Configuration).all()
    if configurations:
        for config in configurations:
            print(f"   ID: {config.id}, Name: {config.name}, Machine ID: {config.machine_id}")
            # 显示关联的测试机名称
            machine = session.query(models.Machine).filter(models.Machine.id == config.machine_id).first()
            if machine:
                print(f"      -> Machine: {machine.name}")
    else:
        print("   No configurations found")
    
    print("\n4. Cards Table:")
    cards = session.query(models.Card).all()
    if cards:
        for card in cards:
            print(f"   ID: {card.id}, Model: {card.model}, Machine ID: {card.machine_id}")
            # 显示关联的测试机名称
            machine = session.query(models.Machine).filter(models.Machine.id == card.machine_id).first()
            if machine:
                print(f"      -> Machine: {machine.name}")
    else:
        print("   No cards found")
    
    print("\n5. Card Types Table:")
    card_types = session.query(models.CardType).all()
    if card_types:
        for card_type in card_types:
            print(f"   ID: {card_type.id}, Name: {card_type.name}, Hourly Rate: {card_type.hourly_rate}")
    else:
        print("   No card types found")
    
    print("\n6. Auxiliary Equipment Table:")
    aux_equipments = session.query(models.AuxiliaryEquipment).all()
    if aux_equipments:
        for equipment in aux_equipments:
            print(f"   ID: {equipment.id}, Name: {equipment.name}, Hourly Rate: {equipment.hourly_rate}")
    else:
        print("   No auxiliary equipment found")
    
    # 展示层级结构
    print("\n=== HIERARCHICAL STRUCTURE ===\n")
    for supplier in suppliers:
        print(f"Supplier: {supplier.name}")
        supplier_machines = session.query(models.Machine).filter(models.Machine.supplier_id == supplier.id).all()
        if supplier_machines:
            for machine in supplier_machines:
                print(f"  └── Machine: {machine.name}")
                
                # 显示配置
                machine_configs = session.query(models.Configuration).filter(models.Configuration.machine_id == machine.id).all()
                if machine_configs:
                    for config in machine_configs:
                        print(f"      └── Configuration: {config.name}")
                else:
                    print("      └── Configurations: None")
                
                # 显示卡片配置
                machine_card_configs = session.query(models.CardConfig).filter(models.CardConfig.machine_id == machine.id).all()
                if machine_card_configs:
                    for card_config in machine_card_configs:
                        print(f"      └── Card Config: {card_config.board_name}")
                else:
                    print("      └── Card Configs: None")
        else:
            print("  └── Machines: None")
        print()
    
    session.close()

if __name__ == "__main__":
    view_database_content()