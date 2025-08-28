#!/usr/bin/env python3
"""
测试数据库连接和表创建
"""

import sys
import os
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# 添加项目路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import engine, SessionLocal, Base
from app.models import *

def test_database():
    """测试数据库连接"""
    print("🔧 测试数据库连接...")
    
    try:
        # 删除所有表
        print("删除旧表...")
        Base.metadata.drop_all(bind=engine)
        
        # 创建所有表
        print("创建新表...")
        Base.metadata.create_all(bind=engine)
        
        # 测试连接
        db = SessionLocal()
        
        # 检查表是否存在
        with engine.connect() as conn:
            tables = conn.execute(text("SELECT name FROM sqlite_master WHERE type='table';")).fetchall()
            print(f"✅ 成功创建 {len(tables)} 个表:")
            for table in tables:
                print(f"   - {table[0]}")
        
        # 创建一个测试报价单
        print("\n📝 创建测试报价单...")
        test_quote = Quote(
            quote_number="QT202408001",
            title="测试报价单",
            quote_type="inquiry",
            customer_name="测试客户",
            currency="CNY",
            total_amount=100000.0,
            status="draft",
            created_by=1
        )
        
        db.add(test_quote)
        db.commit()
        
        # 验证数据
        quotes_count = db.query(Quote).count()
        print(f"✅ 成功创建 {quotes_count} 条报价单记录")
        
        if quotes_count > 0:
            quote = db.query(Quote).first()
            print(f"   报价单号: {quote.quote_number}")
            print(f"   标题: {quote.title}")
            print(f"   状态: {quote.status}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ 数据库测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_database()
    print("\n" + "="*50)
    if success:
        print("🎉 数据库测试成功！")
    else:
        print("❌ 数据库测试失败！")
    sys.exit(0 if success else 1)