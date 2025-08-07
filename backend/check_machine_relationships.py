from app.database import SessionLocal
from app import models

def check_machine_relationships():
    db = SessionLocal()
    
    print("检查机器、供应商和机器类型的关系...")
    
    # 获取所有机器
    machines = db.query(models.Machine).all()
    
    print(f"\n总共 {len(machines)} 台机器:")
    
    for machine in machines:
        print(f"\n机器 ID: {machine.id}")
        print(f"  名称: {machine.name}")
        print(f"  描述: {machine.description}")
        
        # 检查供应商关系
        supplier = machine.supplier
        if supplier:
            print(f"  供应商 ID: {supplier.id}")
            print(f"  供应商名称: {supplier.name}")
            
            # 检查机器类型关系
            machine_type = supplier.machine_type
            if machine_type:
                print(f"  机器类型 ID: {machine_type.id}")
                print(f"  机器类型名称: {machine_type.name}")
            else:
                print(f"  机器类型: None")
        else:
            print(f"  供应商: None")
    
    db.close()

if __name__ == "__main__":
    check_machine_relationships()