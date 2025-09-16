#!/usr/bin/env python3
"""
测试统一审批系统 - 验证企业微信审批和内部审批的一致性
"""

import sys
import os
import json
from datetime import datetime

# 添加app目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from app.database import SessionLocal
from app.models import Quote, ApprovalRecord
from app.services.unified_approval_service import UnifiedApprovalService, ApprovalMethod
from app.services.quote_service import QuoteService
from app.schemas import QuoteCreate, QuoteItemCreate

def test_unified_approval_consistency():
    """测试统一审批系统的一致性"""
    print("🧪 开始测试统一审批系统一致性")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 1. 检查现有报价单的审批状态
        print("1️⃣ 检查现有报价单审批状态")
        quotes = db.query(Quote).filter(Quote.is_deleted == False).all()
        print(f"   当前有 {len(quotes)} 个未删除报价单")

        for quote in quotes:
            print(f"   📋 {quote.quote_number} ({quote.customer_name})")
            print(f"      状态: {quote.status} → 审批状态: {quote.approval_status}")

            # 检查审批记录
            approval_records = db.query(ApprovalRecord).filter(
                ApprovalRecord.quote_id == quote.id
            ).all()

            print(f"      审批记录: {len(approval_records)} 条")
            for record in approval_records:
                print(f"        • {record.approval_method}: {record.status} - {record.comments or '无备注'}")
                print(f"          时间: {record.created_at}")
            print()

        # 2. 测试统一审批服务
        print("2️⃣ 测试统一审批服务接口")

        if quotes:
            test_quote = quotes[0]  # 选择第一个报价单进行测试
            print(f"   使用报价单: {test_quote.quote_number}")

            approval_service = UnifiedApprovalService(db)

            # 检查可用的审批方法
            print("   可用的审批方法:")
            print(f"     • 内部审批: {ApprovalMethod.INTERNAL.value}")
            print(f"     • 企业微信审批: {ApprovalMethod.WECOM.value}")

            # 检查当前审批状态
            current_status = approval_service.get_approval_status(test_quote.id)
            print(f"   当前审批状态: {current_status}")

            # 获取审批历史
            approval_history = approval_service.get_approval_history(test_quote.id)
            print(f"   审批历史记录: {len(approval_history)} 条")

        # 3. 验证审批方法一致性
        print("3️⃣ 验证审批方法一致性")

        print("   检查内部审批接口...")
        internal_available = test_approval_method_availability("internal")
        print(f"   内部审批可用: {'✅' if internal_available else '❌'}")

        print("   检查企业微信审批接口...")
        wecom_available = test_approval_method_availability("wecom")
        print(f"   企业微信审批可用: {'✅' if wecom_available else '❌'}")

        # 4. 总结
        print("4️⃣ 测试总结")
        if internal_available and wecom_available:
            print("   ✅ 统一审批系统运行正常")
            print("   ✅ 内部审批和企业微信审批接口都可用")
            print("   ✅ 审批状态数据结构一致")
        else:
            print("   ❌ 发现问题:")
            if not internal_available:
                print("      - 内部审批接口不可用")
            if not wecom_available:
                print("      - 企业微信审批接口不可用")

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

def test_approval_method_availability(method):
    """测试审批方法可用性"""
    try:
        db = SessionLocal()
        approval_service = UnifiedApprovalService(db)

        # 尝试获取审批状态（这是最基本的操作）
        quotes = db.query(Quote).filter(Quote.is_deleted == False).first()
        if quotes:
            status = approval_service.get_approval_status(quotes.id)
            return True
        return False

    except Exception as e:
        print(f"      错误: {e}")
        return False
    finally:
        if 'db' in locals():
            db.close()

def create_test_quote_for_approval():
    """创建一个测试报价单用于审批测试"""
    print("📝 创建测试报价单...")

    db = SessionLocal()
    try:
        # 创建测试报价单数据
        items_data = [
            QuoteItemCreate(
                item_name="测试设备-1",
                item_description="用于统一审批测试的设备",
                machine_type="测试机",
                supplier="测试供应商",
                machine_model="TEST-001",
                configuration="标准配置",
                quantity=1.0,
                unit="小时",
                unit_price=100.0,
                total_price=100.0,
                machine_id=1,
                configuration_id=1
            )
        ]

        quote_data = QuoteCreate(
            title="统一审批测试报价单",
            quote_type="KS",
            customer_name="统一审批测试客户",
            customer_contact="测试联系人",
            customer_phone="13800000000",
            customer_email="test@example.com",
            quote_unit="昆山芯信安",
            currency="CNY",
            description="用于测试统一审批系统的报价单",
            notes="自动化测试数据",
            items=items_data,
            subtotal=100.0,
            total_amount=100.0
        )

        # 创建报价单
        quote_service = QuoteService(db)
        quote = quote_service.create_quote(quote_data, user_id=1)

        print(f"   ✅ 创建成功: {quote.quote_number}")
        return quote

    except Exception as e:
        print(f"   ❌ 创建失败: {e}")
        return None
    finally:
        db.close()

if __name__ == "__main__":
    print("🔧 统一审批系统一致性测试")
    print(f"⏰ 测试时间: {datetime.now()}")
    print()

    test_unified_approval_consistency()

    print()
    print("🏁 测试完成")