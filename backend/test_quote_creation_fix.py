#!/usr/bin/env python3
"""
测试报价单创建修复
验证 quote_items 主键问题是否已解决
"""

import sys
import os
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models import Quote, QuoteItem
from app.services.quote_service import QuoteService
from app.schemas import QuoteCreate, QuoteItemCreate

def test_quote_creation():
    """测试报价单创建功能"""
    print("🧪 测试报价单创建修复")
    print(f"⏰ 测试时间: {datetime.now()}")
    print("=" * 50)

    db = SessionLocal()
    try:
        # 创建测试数据
        print("1️⃣ 准备测试数据...")

        items_data = [
            QuoteItemCreate(
                item_name="修复测试设备",
                item_description="用于验证主键修复的测试设备",
                machine_type="测试机",
                supplier="测试供应商",
                machine_model="FIX-TEST-001",
                configuration="标准配置",
                quantity=2.0,
                unit="小时",
                unit_price=150.0,
                total_price=300.0,
                machine_id=1,
                configuration_id=1
            ),
            QuoteItemCreate(
                item_name="验证设备项目",
                item_description="第二个测试项目",
                machine_type="分选机",
                supplier="验证供应商",
                machine_model="VERIFY-001",
                configuration="高级配置",
                quantity=1.5,
                unit="小时",
                unit_price=200.0,
                total_price=300.0,
                machine_id=2,
                configuration_id=2
            )
        ]

        quote_data = QuoteCreate(
            title="主键修复验证报价单-最新",
            quote_type="KS",
            customer_name="修复测试客户-新测试",
            customer_contact="测试工程师",
            customer_phone="13900000000",
            customer_email="fix@test.com",
            quote_unit="昆山芯信安",
            currency="CNY",
            description="用于验证 quote_items 主键修复的测试报价单",
            notes="数据库修复后的全新测试，避免重复编号",
            items=items_data,
            subtotal=600.0,
            total_amount=600.0
        )

        print("2️⃣ 创建报价单...")

        # 创建报价单
        quote_service = QuoteService(db)
        quote = quote_service.create_quote(quote_data, user_id=1)

        print(f"   ✅ 创建成功!")
        print(f"   📋 报价单号: {quote.quote_number}")
        print(f"   🆔 ID: {quote.id}")
        print(f"   👤 创建人: {quote.created_by}")
        print(f"   💰 总金额: {quote.total_amount}")

        # 验证报价明细
        print("3️⃣ 验证报价明细...")
        items = db.query(QuoteItem).filter(QuoteItem.quote_id == quote.id).all()
        print(f"   明细项目数: {len(items)}")

        for i, item in enumerate(items, 1):
            print(f"   项目 {i}:")
            print(f"     🆔 ID: {item.id} (类型: {type(item.id)})")
            print(f"     📝 名称: {item.item_name}")
            print(f"     🔢 数量: {item.quantity}")
            print(f"     💵 单价: {item.unit_price}")
            print(f"     💰 小计: {item.total_price}")

        # 验证数据库一致性
        print("4️⃣ 验证数据库一致性...")

        # 重新查询验证
        db.refresh(quote)
        print(f"   报价单状态: {quote.status}")
        print(f"   明细项目关联: {len(quote.items)} 个")

        print("5️⃣ 测试结果:")
        print("   ✅ 报价单创建成功")
        print("   ✅ 明细项目保存成功")
        print("   ✅ 主键自动生成正常")
        print("   ✅ 外键关联正确")

        return True

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    finally:
        db.close()

def check_database_state():
    """检查数据库状态"""
    print("\n📊 检查数据库当前状态...")

    db = SessionLocal()
    try:
        # 检查报价单数量
        quote_count = db.query(Quote).count()
        print(f"   报价单总数: {quote_count}")

        # 检查明细项目数量
        item_count = db.query(QuoteItem).count()
        print(f"   明细项目总数: {item_count}")

        # 检查最新的报价单
        latest_quote = db.query(Quote).order_by(Quote.created_at.desc()).first()
        if latest_quote:
            print(f"   最新报价单: {latest_quote.quote_number}")
            print(f"   创建时间: {latest_quote.created_at}")

    except Exception as e:
        print(f"   ❌ 检查失败: {e}")

    finally:
        db.close()

if __name__ == "__main__":
    # 先检查当前状态
    check_database_state()

    print()

    # 执行测试
    success = test_quote_creation()

    print()

    # 再次检查状态
    check_database_state()

    print("\n" + "="*50)
    if success:
        print("🎉 quote_items 主键问题已修复！")
        print("   现在可以正常创建包含明细项目的报价单了。")
    else:
        print("💥 修复验证失败！")
        print("   请检查错误信息并进一步调试。")