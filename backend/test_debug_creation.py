#!/usr/bin/env python3
"""
调试报价单创建问题
逐步检查创建过程
"""

import sys
import os
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.services.quote_service import QuoteService
from app.schemas import QuoteCreate, QuoteItemCreate

def debug_quote_creation():
    """调试报价单创建过程"""
    print("🔍 调试报价单创建过程")
    print(f"⏰ 调试时间: {datetime.now()}")
    print("=" * 60)

    db = SessionLocal()
    try:
        service = QuoteService(db)

        print("1️⃣ 测试报价单号生成...")
        quote_number = service.generate_quote_number("昆山芯信安")
        print(f"   生成的编号: {quote_number}")

        print("2️⃣ 准备最简单的测试数据...")

        # 最简单的测试数据
        items_data = [
            QuoteItemCreate(
                item_name="调试测试项",
                item_description="最简单的测试项",
                machine_type="测试",
                supplier="测试",
                machine_model="TEST-001",
                configuration="基础",
                quantity=1.0,
                unit="个",
                unit_price=100.0,
                total_price=100.0,
                machine_id=1,
                configuration_id=1
            )
        ]

        quote_data = QuoteCreate(
            title="调试测试",
            quote_type="tooling",
            customer_name="调试客户",
            customer_contact="测试",
            customer_phone="123456",
            customer_email="test@test.com",
            quote_unit="昆山芯信安",
            currency="CNY",
            description="调试测试",
            notes="最简单的调试测试",
            items=items_data,
            subtotal=100.0,
            total_amount=100.0
        )

        print("3️⃣ 逐步执行创建过程...")

        # 手动执行创建步骤
        from app.models import Quote, QuoteItem, ApprovalRecord, User

        # 创建报价单主记录
        quote_dict = quote_data.model_dump(exclude={'items'})
        quote_dict.update({
            'quote_number': quote_number,
            'status': 'draft',
            'created_by': 1,
            'approved_by': None,
            'approved_at': None
        })

        quote = Quote(**quote_dict)
        print(f"   报价单对象创建: {quote.quote_number}")

        db.add(quote)
        print("   添加到会话")

        db.flush()
        print(f"   刷新后ID: {quote.id}")

        # 创建报价明细
        for item_data in quote_data.items:
            item_dict = item_data.model_dump()
            item_dict['quote_id'] = quote.id
            item = QuoteItem(**item_dict)
            db.add(item)
            print(f"   添加明细项: {item.item_name}")

        print("4️⃣ 提交事务...")
        db.commit()
        print("   事务提交成功")

        print("5️⃣ 验证创建结果...")
        saved_quote = db.query(Quote).filter(Quote.quote_number == quote_number).first()

        if saved_quote:
            print(f"   ✅ 报价单保存成功: {saved_quote.quote_number}")
            print(f"   📋 客户: {saved_quote.customer_name}")
            print(f"   💰 金额: {saved_quote.total_amount}")
            print(f"   🆔 ID: {saved_quote.id}")
            return True
        else:
            print("   ❌ 报价单未保存")
            return False

    except Exception as e:
        print(f"❌ 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    success = debug_quote_creation()
    print("\n" + "="*60)
    if success:
        print("🎉 调试成功！找到了创建流程的问题。")
    else:
        print("💥 调试发现问题，需要进一步修复。")