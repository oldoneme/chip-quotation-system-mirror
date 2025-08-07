from app.database import engine
from app.models import Base
from sqlalchemy import MetaData, inspect, text
from sqlalchemy.schema import CreateTable

# 创建一个新的metadata对象
metadata = MetaData()

# 反射现有数据库结构
metadata.reflect(bind=engine)

# 检查card_configs表是否存在
if 'card_configs' in metadata.tables:
    # 获取现有表
    card_configs_table = metadata.tables['card_configs']
    
    # 检查字段是否存在，如果不存在则添加
    with engine.connect() as conn:
        # 添加currency字段
        if 'currency' not in card_configs_table.c:
            print("Adding currency column...")
            conn.execute(text("ALTER TABLE card_configs ADD COLUMN currency VARCHAR(10) DEFAULT 'RMB'"))
        
        # 添加exchange_rate字段
        if 'exchange_rate' not in card_configs_table.c:
            print("Adding exchange_rate column...")
            conn.execute(text("ALTER TABLE card_configs ADD COLUMN exchange_rate FLOAT DEFAULT 1.0"))
        
        conn.commit()
        print("Migration completed successfully!")
else:
    print("card_configs table not found. Creating table with new schema...")
    # 如果表不存在，则创建新表
    Base.metadata.create_all(bind=engine)
    print("Table created successfully!")