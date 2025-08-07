import json
from sqlalchemy.orm import joinedload
from app.database import SessionLocal
from app import models
from app.schemas import Machine

def test_api_response():
    db = SessionLocal()
    
    # 模拟API查询，加载关系
    machines = db.query(models.Machine).options(
        joinedload(models.Machine.supplier).joinedload(models.Supplier.machine_type)
    ).all()
    
    print("API响应模拟测试:")
    print(f"总共获取到 {len(machines)} 台机器")
    
    # 序列化为JSON，模拟API响应
    machines_data = []
    for machine in machines:
        try:
            # 使用Pydantic模型序列化
            machine_schema = Machine.from_orm(machine)
            machines_data.append(machine_schema.dict())
        except Exception as e:
            print(f"序列化机器 {machine.name} 时出错: {e}")
    
    print("\n序列化后的数据示例 (前3个):")
    for i, machine_data in enumerate(machines_data[:3]):
        print(f"\n机器 {i+1}:")
        print(json.dumps(machine_data, indent=2, ensure_ascii=False))
    
    db.close()

if __name__ == "__main__":
    test_api_response()