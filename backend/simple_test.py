import sys
import os

# Add the project root directory to the path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

# 导入必要的模块
from app.database import SessionLocal
from app import models

def check_database():
    print("检查数据库内容...")
    try:
        db = SessionLocal()
        machine_types_count = db.query(models.MachineType).count()
        suppliers_count = db.query(models.Supplier).count()
        machines_count = db.query(models.Machine).count()
        card_configs_count = db.query(models.CardConfig).count()
        
        print(f"MachineTypes 表中有 {machine_types_count} 条记录")
        print(f"Suppliers 表中有 {suppliers_count} 条记录")
        print(f"Machines 表中有 {machines_count} 条记录")
        print(f"CardConfigs 表中有 {card_configs_count} 条记录")
        
        # 显示一些具体数据
        if machine_types_count > 0:
            machine_types = db.query(models.MachineType).limit(5).all()
            print("\n前5个机器类型:")
            for mt in machine_types:
                print(f"  - ID: {mt.id}, Name: {mt.name}")
        
        db.close()
    except Exception as e:
        print(f"检查数据库时出错: {e}")

def check_imports():
    print("\n检查关键模块导入...")
    try:
        from app.main import app
        print("✓ 主应用导入成功")
    except Exception as e:
        print(f"✗ 主应用导入失败: {e}")
    
    try:
        from app.api.v1.api import api_router
        print("✓ API路由导入成功")
    except Exception as e:
        print(f"✗ API路由导入失败: {e}")
    
    try:
        from app.api.v1.endpoints import machine_types, suppliers, card_configs
        print("✓ 端点模块导入成功")
    except Exception as e:
        print(f"✗ 端点模块导入失败: {e}")

if __name__ == "__main__":
    check_imports()
    check_database()