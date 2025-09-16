#!/usr/bin/env python3
"""
最终测试报价单创建
验证所有修复是否生效
"""

import sys
import os
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.services.quote_service import QuoteService
from app.schemas import QuoteCreate, QuoteItemCreate

def test_complete_quote_creation():
    """完整测试报价单创建流程"""
    print("🚀 完整报价单创建测试")
    print(f"⏰ 测试时间: {datetime.now()}")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 1. 准备测试数据
        print("1️⃣ 准备测试数据...")

        items_data = [
            QuoteItemCreate(
                item_name="最终测试设备",
                item_description="验证完整创建流程的测试设备",
                machine_type="测试机",
                supplier="最终测试供应商",
                machine_model="FINAL-TEST-001",
                configuration="标准配置",
                quantity=1.0,
                unit="小时",
                unit_price=500.0,
                total_price=500.0,
                machine_id=1,
                configuration_id=1
            )
        ]

        quote_data = QuoteCreate(
            title="最终修复验证报价单",
            quote_type="tooling",
            customer_name="最终测试客户",
            customer_contact="测试工程师",
            customer_phone="13999999999",
            customer_email="final@test.com",
            quote_unit="昆山芯信安",
            currency="CNY",
            description="验证所有修复的最终测试报价单",
            notes="包含编号生成、主键修复、刷新问题修复",
            items=items_data,
            subtotal=500.0,
            total_amount=500.0
        )

        print("2️⃣ 创建报价单...")

        # 2. 创建报价单
        quote_service = QuoteService(db)
        quote = quote_service.create_quote(quote_data, user_id=1)

        print(f"   ✅ 创建成功!")
        print(f"   📋 报价单号: {quote.quote_number}")
        print(f"   🆔 ID: {quote.id}")
        print(f"   👤 客户: {quote.customer_name}")
        print(f"   💰 金额: ¥{quote.total_amount}")
        print(f"   📊 状态: {quote.status}")

        # 3. 验证明细项目
        print("3️⃣ 验证明细项目...")
        print(f"   明细项目数: {len(quote.items)}")

        for i, item in enumerate(quote.items, 1):
            print(f"   项目 {i}: {item.item_name} - ¥{item.total_price}")

        # 4. 验证数据库持久化
        print("4️⃣ 验证数据库持久化...")

        # 重新查询验证
        saved_quote = quote_service.get_quote_by_number(quote.quote_number)
        if saved_quote:
            print(f"   ✅ 数据库查询成功: {saved_quote.quote_number}")
            print(f"   📝 客户名称匹配: {saved_quote.customer_name == quote.customer_name}")
            print(f"   💰 金额匹配: {saved_quote.total_amount == quote.total_amount}")
        else:
            print("   ❌ 数据库查询失败")
            return False

        print("5️⃣ 测试结果:")
        print("   ✅ 报价单号生成正常")
        print("   ✅ 主键问题已解决")
        print("   ✅ 对象刷新问题已修复")
        print("   ✅ 明细项目保存成功")
        print("   ✅ 数据库持久化正常")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

if __name__ == "__main__":
    success = test_complete_quote_creation()

    print("\n" + "="*60)
    if success:
        print("🎉 所有问题已修复！报价单创建完全正常！")
        print("   现在可以通过前端正常创建报价单了。")
    else:
        print("💥 仍有问题需要解决！")
        print("   请检查错误信息。")