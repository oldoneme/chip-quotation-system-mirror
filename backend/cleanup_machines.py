from app.database import SessionLocal
from app import models

def cleanup_invalid_machines():
    db = SessionLocal()
    
    print("清理数据库中的无效机器...")
    
    # 查找没有供应商的机器
    invalid_machines = db.query(models.Machine).filter(
        models.Machine.supplier_id.is_(None)
    ).all()
    
    print(f"找到 {len(invalid_machines)} 台没有供应商的机器:")
    for machine in invalid_machines:
        print(f"  ID: {machine.id}, 名称: {machine.name}, 描述: {machine.description}")
    
    # 删除这些机器
    for machine in invalid_machines:
        print(f"删除机器: {machine.name} (ID: {machine.id})")
        db.delete(machine)
    
    db.commit()
    print("清理完成!")
    
    # 显示清理后的机器列表
    remaining_machines = db.query(models.Machine).all()
    print(f"\n清理后剩余 {len(remaining_machines)} 台机器:")
    for machine in remaining_machines:
        supplier = machine.supplier
        if supplier:
            machine_type = supplier.machine_type
            if machine_type:
                print(f"  ID: {machine.id}, 名称: {machine.name}, 供应商: {supplier.name}, 类型: {machine_type.name}")
            else:
                print(f"  ID: {machine.id}, 名称: {machine.name}, 供应商: {supplier.name}, 类型: None")
        else:
            print(f"  ID: {machine.id}, 名称: {machine.name}, 供应商: None")
    
    db.close()

if __name__ == "__main__":
    cleanup_invalid_machines()