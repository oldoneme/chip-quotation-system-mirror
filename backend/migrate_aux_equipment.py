from app.database import engine
from app.models import Base
from sqlalchemy import MetaData, text

# 创建一个新的metadata对象
metadata = MetaData()

# 反射现有数据库结构
metadata.reflect(bind=engine)

# 检查auxiliary_equipment表是否存在
if 'auxiliary_equipment' in metadata.tables:
    # 获取现有表
    aux_equipment_table = metadata.tables['auxiliary_equipment']
    
    # 检查type字段是否存在，如果不存在则添加
    with engine.connect() as conn:
        # 添加type字段
        if 'type' not in aux_equipment_table.c:
            print("Adding type column...")
            conn.execute(text("ALTER TABLE auxiliary_equipment ADD COLUMN type VARCHAR(50)"))
        
        conn.commit()
        print("Migration completed successfully!")
else:
    print("auxiliary_equipment table not found. Creating table with new schema...")
    Base.metadata.create_all(bind=engine)