from app.database import SessionLocal
from app import models

def update_aux_equipment_types():
    db = SessionLocal()
    try:
        # 获取所有辅助设备
        devices = db.query(models.AuxiliaryEquipment).all()
        
        for device in devices:
            # 根据名称设置类型
            if 'Handler' in device.name or 'F550' in device.name:
                device.type = 'handler'
            elif 'Prober' in device.name:
                device.type = 'prober'
            else:
                device.type = 'handler'  # 默认设置为handler
            
            print(f'Updated {device.name} with type {device.type}')
        
        # 提交更改
        db.commit()
        print("All auxiliary equipment updated successfully!")
        
    except Exception as e:
        print(f"Error updating auxiliary equipment: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_aux_equipment_types()