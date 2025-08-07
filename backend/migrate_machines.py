from app.database import engine
from app.models import Base
from sqlalchemy import MetaData, text

# 创建一个新的metadata对象
metadata = MetaData()

# 反射现有数据库结构
metadata.reflect(bind=engine)

# 检查machines表是否存在
if 'machines' in metadata.tables:
    # 获取现有表
    machines_table = metadata.tables['machines']
    
    # 检查字段是否存在，如果不存在则添加
    with engine.connect() as conn:
        # 添加currency字段
        if 'currency' not in machines_table.c:
            print("Adding currency column...")
            conn.execute(text("ALTER TABLE machines ADD COLUMN currency VARCHAR(10) DEFAULT 'RMB'"))
        
        conn.commit()
        print("Migration completed successfully!")
else:
    print("machines table not found. Creating table with new schema...")
    # 如果表不存在，则创建新表
    Base.metadata.create_all(bind=engine)
    print("Table created successfully!")