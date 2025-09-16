#!/usr/bin/env python3
"""
全面诊断报价单创建问题的脚本
分析数据库状态、表结构和现有数据
"""

import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import QuoteItem, Quote, User
from sqlalchemy import inspect, text, MetaData
import traceback

def main():
    print("🔍 全面诊断报价单创建问题")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 1. 检查数据库文件是否存在
        print("1️⃣ 检查数据库文件:")
        db_path = "/home/qixin/projects/chip-quotation-system/backend/app/test.db"
        if os.path.exists(db_path):
            print(f"   ✅ 数据库文件存在: {db_path}")
            size = os.path.getsize(db_path)
            print(f"   📊 文件大小: {size} bytes")
        else:
            print(f"   ❌ 数据库文件不存在: {db_path}")

        # 2. 检查表是否存在
        print("\n2️⃣ 检查数据库表:")
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print(f"   现有表: {tables}")

        if 'quotes' in tables:
            print("   ✅ quotes表存在")
        else:
            print("   ❌ quotes表不存在")

        if 'quote_items' in tables:
            print("   ✅ quote_items表存在")
        else:
            print("   ❌ quote_items表不存在")

        # 3. 检查quote_items表结构
        print("\n3️⃣ 检查quote_items表结构:")
        if 'quote_items' in tables:
            columns = inspector.get_columns('quote_items')
            for col in columns:
                pk_info = "(primary_key)" if col.get('primary_key', False) else ""
                auto_info = f"(autoincrement: {col.get('autoincrement', 'default')})" if col.get('primary_key', False) else ""
                print(f"   - {col['name']}: {col['type']} {pk_info} {auto_info}")

            # 检查主键约束
            pk = inspector.get_pk_constraint('quote_items')
            print(f"   Primary Key constraint: {pk}")

        # 4. 检查quotes表结构和现有数据
        print("\n4️⃣ 检查quotes表现有数据:")
        if 'quotes' in tables:
            quotes = db.query(Quote).all()
            print(f"   现有Quote记录数: {len(quotes)}")
            for quote in quotes:
                print(f"   - ID: {quote.id}, 编号: {quote.quote_number}, 状态: {quote.status}")

        # 5. 检查quote_items表现有数据
        print("\n5️⃣ 检查quote_items表现有数据:")
        if 'quote_items' in tables:
            # 直接SQL查询
            items_sql = db.execute(text("SELECT * FROM quote_items")).fetchall()
            print(f"   SQL查询到的记录数: {len(items_sql)}")

            # ORM查询
            try:
                items_orm = db.query(QuoteItem).all()
                print(f"   ORM查询到的记录数: {len(items_orm)}")
                for item in items_orm:
                    print(f"   - ID: {item.id}, Quote_ID: {item.quote_id}, Item: {item.item_name}")
            except Exception as e:
                print(f"   ❌ ORM查询失败: {e}")

        # 6. 测试QuoteItem创建
        print("\n6️⃣ 测试QuoteItem对象创建:")
        try:
            # 检查是否有Quote可用
            quotes = db.query(Quote).all()
            if quotes:
                quote = quotes[0]
                print(f"   使用Quote ID: {quote.id}")

                # 创建测试QuoteItem数据
                test_data = {
                    'quote_id': quote.id,
                    'item_name': 'Test Item',
                    'item_description': 'Test Description',
                    'machine_type': 'Test Machine',
                    'supplier': 'Test Supplier',
                    'machine_model': 'Test Model',
                    'configuration': 'Test Config',
                    'quantity': 1.0,
                    'unit': 'hours',
                    'unit_price': 100.0,
                    'total_price': 100.0
                }

                # 创建QuoteItem对象但不保存
                test_item = QuoteItem(**test_data)
                print(f"   ✅ QuoteItem对象创建成功")
                print(f"   对象ID: {test_item.id}")
                print(f"   Quote_ID: {test_item.quote_id}")

                # 尝试添加到session但不提交
                db.add(test_item)
                print(f"   ✅ 已添加到session")

                # 尝试flush
                try:
                    db.flush()
                    print(f"   ✅ flush成功，生成ID: {test_item.id}")
                    db.rollback()  # 回滚测试数据
                except Exception as flush_e:
                    print(f"   ❌ flush失败: {flush_e}")
                    db.rollback()

            else:
                print("   ⚠️ 没有Quote记录可用于测试")

        except Exception as e:
            print(f"   ❌ QuoteItem创建测试失败: {e}")
            db.rollback()

        # 7. 检查报价单号冲突
        print("\n7️⃣ 检查报价单号冲突:")
        try:
            # 查找重复的报价单号
            duplicate_numbers = db.execute(text("""
                SELECT quote_number, COUNT(*) as count
                FROM quotes
                GROUP BY quote_number
                HAVING COUNT(*) > 1
            """)).fetchall()

            if duplicate_numbers:
                print("   ❌ 发现重复的报价单号:")
                for row in duplicate_numbers:
                    print(f"   - {row.quote_number}: {row.count} 次")
            else:
                print("   ✅ 没有重复的报价单号")

            # 检查今日报价单号
            today_quotes = db.execute(text("""
                SELECT quote_number FROM quotes
                WHERE quote_number LIKE 'CIS-KS20250916%'
                ORDER BY quote_number
            """)).fetchall()

            print(f"   今日报价单号 (CIS-KS20250916%):")
            for row in today_quotes:
                print(f"   - {row.quote_number}")

        except Exception as e:
            print(f"   ❌ 报价单号检查失败: {e}")

        # 8. 检查SQLAlchemy版本和配置
        print("\n8️⃣ 环境信息:")
        import sqlalchemy
        print(f"   SQLAlchemy版本: {sqlalchemy.__version__}")
        print(f"   Engine: {engine}")
        print(f"   连接URL: {engine.url}")

    except Exception as e:
        print(f"\n❌ 诊断过程出错: {e}")
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    main()