#!/usr/bin/env python3
"""
直接验证 quote_items 主键修复
测试QuoteItem创建不再有NULL identity key错误
"""

import sys
import os
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models import QuoteItem

def test_quote_item_primary_key():
    """直接测试QuoteItem主键是否正常工作"""
    print("🧪 测试 QuoteItem 主键修复")
    print(f"⏰ 测试时间: {datetime.now()}")
    print("=" * 50)

    db = SessionLocal()
    try:
        print("1️⃣ 创建新的 QuoteItem...")

        # 直接创建QuoteItem测试主键
        item = QuoteItem(
            quote_id="test-quote-id",
            item_name="测试项目",
            item_description="验证主键修复的测试项目",
            machine_type="测试机",
            supplier="测试供应商",
            machine_model="TEST-001",
            configuration="基础配置",
            quantity=1.0,
            unit="小时",
            unit_price=100.0,
            total_price=100.0,
            machine_id=1,
            configuration_id=1
        )

        db.add(item)
        db.flush()  # 这里之前会出现NULL identity key错误

        print(f"   ✅ 成功创建 QuoteItem!")
        print(f"   🆔 ID: {item.id} (类型: {type(item.id)})")
        print(f"   📝 名称: {item.item_name}")
        print(f"   💰 价格: {item.total_price}")

        # 验证ID是整数且不为None
        if item.id is None:
            raise ValueError("主键ID为None!")
        if not isinstance(item.id, int):
            raise ValueError(f"主键ID类型错误: {type(item.id)}, 应该为int")

        db.commit()

        print("2️⃣ 验证数据库记录...")
        # 重新查询验证
        saved_item = db.query(QuoteItem).filter(QuoteItem.id == item.id).first()
        if not saved_item:
            raise ValueError("无法查询到保存的记录!")

        print(f"   📊 数据库中的记录:")
        print(f"      ID: {saved_item.id}")
        print(f"      名称: {saved_item.item_name}")
        print(f"      价格: {saved_item.total_price}")

        print("3️⃣ 测试结果:")
        print("   ✅ QuoteItem 主键自动生成正常")
        print("   ✅ 不再出现 NULL identity key 错误")
        print("   ✅ 主键类型为整数")
        print("   ✅ 数据库记录保存成功")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    success = test_quote_item_primary_key()

    print("\n" + "="*50)
    if success:
        print("🎉 QuoteItem 主键修复验证成功!")
        print("   可以正常创建包含明细项目的报价单了。")
    else:
        print("💥 主键修复验证失败!")
        print("   需要进一步检查数据库结构。")