#!/usr/bin/env python3
"""
直接测试所有报价类型的创建功能
使用服务层直接测试，避免认证问题
"""

import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models import Quote, QuoteItem, User
from app.services.quote_service import QuoteService
from app.schemas import QuoteCreate, QuoteItemCreate

def test_quote_type_direct(quote_type, description):
    """直接测试指定类型的报价单创建"""
    print(f"\n🧪 测试 {quote_type} 报价类型...")
    print(f"   描述: {description}")

    db = SessionLocal()
    try:
        # 创建报价服务
        service = QuoteService(db)

        # 创建测试数据
        items_data = [
            QuoteItemCreate(
                item_name="ETS-88",
                item_description="FT测试机 - Teradyne",
                machine_type="测试机",
                supplier="Teradyne",
                machine_model="ETS-88",
                configuration="标准配置",
                quantity=1.0,
                unit="小时",
                unit_price=100.0,
                total_price=100.0,
                machine_id=1,
                configuration_id=1
            ),
            QuoteItemCreate(
                item_name="JHT6080",
                item_description="FT分选机 - 金海通",
                machine_type="分选机",
                supplier="金海通",
                machine_model="JHT6080",
                configuration="标准配置",
                quantity=1.0,
                unit="小时",
                unit_price=50.0,
                total_price=50.0,
                machine_id=2,
                configuration_id=2
            )
        ]

        quote_data = QuoteCreate(
            title=f"测试{description} - TestQuote",
            quote_type=quote_type,
            customer_name=f"Test Customer {quote_type.upper()}",
            customer_contact="张先生",
            customer_phone="13812345678",
            customer_email="test@example.com",
            quote_unit="昆山芯信安",
            currency="CNY",
            description=f"测试{description}的创建功能",
            notes=f"自动化测试 - {quote_type}",
            items=items_data,
            subtotal=150.0,
            total_amount=150.0
        )

        # 测试用户ID（假设第一个用户是测试用户）
        user = db.query(User).first()
        if not user:
            print(f"   ❌ 没有找到测试用户")
            return False

        # 创建报价单
        quote = service.create_quote(quote_data, user.id)

        print(f"   ✅ {quote_type} 创建成功")
        print(f"   📋 报价单号: {quote.quote_number}")
        print(f"   🆔 ID: {quote.id}")
        print(f"   📊 状态: {quote.status}")
        print(f"   👤 创建人: {user.username}")

        return True

    except Exception as e:
        print(f"   ❌ {quote_type} 创建失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

def main():
    print("🔧 直接测试所有报价类型的创建功能")
    print("=" * 50)

    # 定义所有报价类型
    quote_types = {
        "inquiry": "询价报价",
        "tooling": "工装报价",
        "engineering": "工程报价",
        "mass_production": "量产报价",
        "process": "工艺报价",
        "comprehensive": "综合报价"
    }

    success_count = 0
    total_count = len(quote_types)

    # 测试每种报价类型
    for quote_type, description in quote_types.items():
        if test_quote_type_direct(quote_type, description):
            success_count += 1

    # 汇总结果
    print(f"\n📊 测试结果汇总:")
    print(f"   ✅ 成功: {success_count}/{total_count}")
    print(f"   ❌ 失败: {total_count - success_count}/{total_count}")

    if success_count == total_count:
        print("\n🎉 所有报价类型测试通过！")
    else:
        print(f"\n⚠️ 有 {total_count - success_count} 个报价类型测试失败")

    # 检查数据库中的结果
    print(f"\n🗄️ 数据库验证:")
    db = SessionLocal()
    try:
        quotes = db.query(Quote).order_by(Quote.id.desc()).limit(10).all()
        items = db.query(QuoteItem).count()
        print(f"   报价单总数: {db.query(Quote).count()}")
        print(f"   报价项目总数: {items}")

        print(f"   最近创建的报价单:")
        for quote in quotes:
            print(f"   - ID:{quote.id}, 类型:{quote.quote_type}, 编号:{quote.quote_number}, 状态:{quote.status}")
    finally:
        db.close()

if __name__ == "__main__":
    main()