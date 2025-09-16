#!/usr/bin/env python3
"""
修复报价单表schema不匹配的脚本
问题：quotes.id是TEXT类型(UUID), 但quote_items.quote_id是INTEGER
解决：统一修改quotes表的id为INTEGER自增主键，重新映射数据
"""

import sys
import os
import uuid

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal, engine
from app.models import Quote, QuoteItem, ApprovalRecord
from sqlalchemy import text
import traceback

def main():
    print("🔧 修复报价单表schema不匹配问题")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 1. 备份现有数据
        print("1️⃣ 备份现有quotes表数据...")
        quotes_data = db.execute(text("SELECT * FROM quotes")).fetchall()
        print(f"   找到 {len(quotes_data)} 条Quote记录")

        quote_items_data = db.execute(text("SELECT * FROM quote_items")).fetchall()
        print(f"   找到 {len(quote_items_data)} 条QuoteItem记录")

        approval_records_data = db.execute(text("SELECT * FROM approval_records")).fetchall()
        print(f"   找到 {len(approval_records_data)} 条ApprovalRecord记录")

        # 2. 创建UUID到INTEGER的映射
        print("2️⃣ 创建UUID到INTEGER的映射...")
        uuid_to_int_mapping = {}
        for i, quote in enumerate(quotes_data, 1):
            uuid_to_int_mapping[quote.id] = i
            print(f"   {quote.id} -> {i} ({quote.quote_number})")

        # 3. 保存数据到Python结构
        print("3️⃣ 转换数据结构...")
        quotes_backup = []
        for quote in quotes_data:
            # 将SQLAlchemy Row转换为字典
            quote_dict = dict(quote._mapping)
            # 删除旧的UUID id，让数据库自动生成新的INTEGER id
            old_uuid = quote_dict.pop('id')
            quote_dict['new_id'] = uuid_to_int_mapping[old_uuid]
            quotes_backup.append(quote_dict)

        quote_items_backup = []
        for item in quote_items_data:
            # 将SQLAlchemy Row转换为字典
            item_dict = dict(item._mapping)
            # 更新外键引用
            old_quote_uuid = item_dict['quote_id']
            if old_quote_uuid in uuid_to_int_mapping:
                item_dict['quote_id'] = uuid_to_int_mapping[old_quote_uuid]
                # 删除id让数据库自动生成
                item_dict.pop('id', None)
                quote_items_backup.append(item_dict)
            else:
                print(f"   ⚠️ 无法找到quote_id映射: {old_quote_uuid}")

        approval_records_backup = []
        for record in approval_records_data:
            # 将SQLAlchemy Row转换为字典
            record_dict = dict(record._mapping)
            # 更新外键引用
            old_quote_uuid = record_dict['quote_id']
            if old_quote_uuid in uuid_to_int_mapping:
                record_dict['quote_id'] = uuid_to_int_mapping[old_quote_uuid]
                # 删除id让数据库自动生成
                record_dict.pop('id', None)
                approval_records_backup.append(record_dict)

        print(f"   转换完成: {len(quotes_backup)} quotes, {len(quote_items_backup)} items, {len(approval_records_backup)} records")

        # 4. 删除现有表
        print("4️⃣ 删除现有表...")
        # 删除有外键依赖的表
        db.execute(text("DELETE FROM approval_records"))
        db.execute(text("DELETE FROM quote_items"))
        db.execute(text("DELETE FROM quotes"))
        db.commit()

        # 删除并重建quotes表
        db.execute(text("DROP TABLE IF EXISTS quotes"))
        db.execute(text("DROP TABLE IF EXISTS quote_items"))
        db.execute(text("DROP TABLE IF EXISTS approval_records"))
        db.commit()
        print("   ✅ 旧表已删除")

        # 5. 重新创建表
        print("5️⃣ 重新创建表...")
        Quote.__table__.create(engine)
        QuoteItem.__table__.create(engine)
        ApprovalRecord.__table__.create(engine)
        print("   ✅ 新表已创建")

        # 6. 验证新表结构
        print("6️⃣ 验证新表结构...")
        quotes_schema = db.execute(text("PRAGMA table_info(quotes)")).fetchall()
        id_column = next((col for col in quotes_schema if col[1] == 'id'), None)
        if id_column and id_column[2] == 'INTEGER':
            print("   ✅ quotes.id字段类型已修复为INTEGER")
        else:
            print(f"   ❌ quotes.id字段类型仍然不正确: {id_column}")

        quote_items_schema = db.execute(text("PRAGMA table_info(quote_items)")).fetchall()
        quote_id_column = next((col for col in quote_items_schema if col[1] == 'quote_id'), None)
        if quote_id_column and quote_id_column[2] == 'INTEGER':
            print("   ✅ quote_items.quote_id字段类型为INTEGER")
        else:
            print(f"   ❌ quote_items.quote_id字段类型不正确: {quote_id_column}")

        # 7. 恢复数据
        print("7️⃣ 恢复数据...")

        # 恢复quotes数据（使用预分配的ID）
        for quote_data in quotes_backup:
            new_id = quote_data.pop('new_id')
            # 手动插入指定ID
            columns = ', '.join(quote_data.keys()) + ', id'
            placeholders = ', '.join(['?' for _ in quote_data.keys()]) + ', ?'
            values = list(quote_data.values()) + [new_id]

            sql = f"INSERT INTO quotes ({columns}) VALUES ({placeholders})"
            db.execute(text(sql), tuple(values))

        db.commit()
        print(f"   ✅ 已恢复 {len(quotes_backup)} 条Quote记录")

        # 恢复quote_items数据
        for item_data in quote_items_backup:
            # 过滤掉None值
            clean_data = {k: v for k, v in item_data.items() if v is not None}
            new_item = QuoteItem(**clean_data)
            db.add(new_item)

        db.commit()
        print(f"   ✅ 已恢复 {len(quote_items_backup)} 条QuoteItem记录")

        # 恢复approval_records数据
        for record_data in approval_records_backup:
            # 过滤掉None值
            clean_data = {k: v for k, v in record_data.items() if v is not None}
            new_record = ApprovalRecord(**clean_data)
            db.add(new_record)

        db.commit()
        print(f"   ✅ 已恢复 {len(approval_records_backup)} 条ApprovalRecord记录")

        # 8. 验证修复结果
        print("8️⃣ 验证修复结果...")

        quotes_count = db.query(Quote).count()
        items_count = db.query(QuoteItem).count()
        records_count = db.query(ApprovalRecord).count()

        print(f"   数据验证:")
        print(f"   - Quotes: {quotes_count} 条记录")
        print(f"   - QuoteItems: {items_count} 条记录")
        print(f"   - ApprovalRecords: {records_count} 条记录")

        # 测试外键关系
        try:
            first_quote = db.query(Quote).first()
            if first_quote:
                print(f"   ✅ 第一个Quote ID: {first_quote.id} (类型: {type(first_quote.id)})")
                items = db.query(QuoteItem).filter(QuoteItem.quote_id == first_quote.id).all()
                print(f"   ✅ 关联的QuoteItems: {len(items)} 条")
            else:
                print("   ⚠️ 没有Quote记录")
        except Exception as e:
            print(f"   ❌ 外键关系测试失败: {e}")

        print("\n🎉 Schema修复完成！")

    except Exception as e:
        print(f"\n❌ 修复失败: {e}")
        print("错误详情:")
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()