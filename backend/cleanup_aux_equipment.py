from app.database import SessionLocal
from app import models

def cleanup_auxiliary_equipment():
    """清理 auxiliary_equipment 表中的测试数据"""
    session = SessionLocal()
    
    try:
        # 显示当前的辅助设备数据
        print("=== 当前辅助设备数据 ===")
        aux_equipments = session.query(models.AuxiliaryEquipment).all()
        for equipment in aux_equipments:
            print(f"ID: {equipment.id}, Name: {equipment.name}, Type: {equipment.type}, Hourly Rate: {equipment.hourly_rate}")
        
        print(f"\n总共有 {len(aux_equipments)} 条辅助设备数据")
        
        # 删除所有测试数据
        if aux_equipments:
            deleted_count = session.query(models.AuxiliaryEquipment).delete()
            session.commit()
            print(f"\n已删除 {deleted_count} 条辅助设备测试数据")
        else:
            print("\n没有找到需要删除的数据")
            
        # 确认删除后的状态
        remaining = session.query(models.AuxiliaryEquipment).count()
        print(f"删除后剩余数据条数: {remaining}")
        
    except Exception as e:
        print(f"清理过程中发生错误: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    cleanup_auxiliary_equipment()