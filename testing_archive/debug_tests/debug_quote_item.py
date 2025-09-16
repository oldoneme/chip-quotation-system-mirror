#!/usr/bin/env python3
"""
调试QuoteItem NULL identity key错误的诊断脚本
"""

import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import QuoteItem, Quote
from sqlalchemy import inspect, text
import traceback

def main():
    print("🔍 QuoteItem NULL identity key 错误诊断")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 1. 检查表结构
        print("1️⃣ 检查quote_items表结构:")
        inspector = inspect(engine)
        columns = inspector.get_columns('quote_items')
        for col in columns:
            print(f"   - {col['name']}: {col['type']} (primary_key: {col.get('primary_key', False)}, autoincrement: {col.get('autoincrement', 'default')})")

        # 2. 检查主键约束
        print("\n2️⃣ 检查主键约束:")
        pk = inspector.get_pk_constraint('quote_items')
        print(f"   Primary Key: {pk}")

        # 3. 检查外键约束
        print("\n3️⃣ 检查外键约束:")
        fks = inspector.get_foreign_keys('quote_items')
        for fk in fks:
            print(f"   Foreign Key: {fk}")

        # 4. 检查当前数据
        print("\n4️⃣ 检查现有数据:")
        quote_items = db.query(QuoteItem).all()
        print(f"   现有QuoteItem记录数: {len(quote_items)}")

        # 5. 模拟创建QuoteItem的过程
        print("\n5️⃣ 模拟创建QuoteItem过程:")

        # 首先检查是否有Quote记录
        quotes = db.query(Quote).all()
        print(f"   现有Quote记录数: {len(quotes)}")

        if quotes:
            quote = quotes[0]
            print(f"   使用第一个Quote ID: {quote.id}")

            # 尝试创建QuoteItem
            print("   尝试创建QuoteItem...")
            test_item_data = {
                'quote_id': quote.id,
                'item_name': 'Test Item',
                'item_description': 'Test Description',
                'machine_type': 'Test Machine',
                'supplier': 'Test Supplier',
                'machine_model': 'Test Model',
                'configuration': 'Test Config',
                'quantity': 1.0,
                'unit': '小时',
                'unit_price': 100.0,
                'total_price': 100.0
            }

            # 检查是否有id字段传入
            if 'id' in test_item_data:
                print("   ⚠️ 发现id字段在数据中")
            else:
                print("   ✅ 没有id字段在数据中")

            test_item = QuoteItem(**test_item_data)
            print(f"   创建的QuoteItem对象ID: {test_item.id}")
            print(f"   对象状态: {test_item in db}")

            # 不实际添加到数据库，只是测试创建过程
            print("   ✅ QuoteItem对象创建成功")
        else:
            print("   ⚠️ 没有Quote记录可用于测试")

    except Exception as e:
        print(f"\n❌ 错误: {e}")
        print(f"错误详情:")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()