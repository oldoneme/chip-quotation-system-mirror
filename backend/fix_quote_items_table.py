#!/usr/bin/env python3
"""
修复quote_items表结构的脚本
将TEXT类型的id字段改为INTEGER自增主键
"""

import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import QuoteItem
from sqlalchemy import text
import traceback

def main():
    print("🔧 修复quote_items表结构")
    print("=" * 40)

    db = SessionLocal()
    try:
        # 1. 备份现有数据
        print("1️⃣ 备份现有数据...")
        existing_items = db.execute(text("SELECT * FROM quote_items")).fetchall()
        print(f"   找到 {len(existing_items)} 条现有记录")

        # 保存数据到临时变量
        backup_data = []
        for item in existing_items:
            backup_data.append({
                'quote_id': item.quote_id,
                'item_name': item.item_name,
                'item_description': item.item_description,
                'machine_type': item.machine_type,
                'supplier': item.supplier,
                'machine_model': item.machine_model,
                'configuration': item.configuration,
                'quantity': item.quantity,
                'unit': item.unit,
                'unit_price': item.unit_price,
                'total_price': item.total_price,
                'machine_id': item.machine_id,
                'configuration_id': item.configuration_id
            })

        # 2. 删除现有表
        print("2️⃣ 删除现有表...")
        db.execute(text("DROP TABLE IF EXISTS quote_items"))
        db.commit()
        print("   ✅ 旧表已删除")

        # 3. 重新创建表
        print("3️⃣ 重新创建表...")
        QuoteItem.__table__.create(engine)
        print("   ✅ 新表已创建")

        # 4. 恢复数据
        print("4️⃣ 恢复数据...")
        for item_data in backup_data:
            # 过滤掉None值
            clean_data = {k: v for k, v in item_data.items() if v is not None}
            new_item = QuoteItem(**clean_data)
            db.add(new_item)

        db.commit()
        print(f"   ✅ 已恢复 {len(backup_data)} 条记录")

        # 5. 验证修复结果
        print("5️⃣ 验证修复结果...")
        # 检查表结构
        result = db.execute(text("PRAGMA table_info(quote_items)")).fetchall()
        id_column = next((col for col in result if col.name == 'id'), None)
        if id_column and 'INTEGER' in str(id_column.type):
            print("   ✅ id字段类型已修复为INTEGER")
        else:
            print("   ❌ id字段类型仍然不正确")

        # 检查数据数量
        count = db.query(QuoteItem).count()
        print(f"   ✅ 数据验证: {count} 条记录")

        print("\n🎉 修复完成！")

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        print("错误详情:")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()