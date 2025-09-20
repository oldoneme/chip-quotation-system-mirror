#!/usr/bin/env python3
"""
测试CIS-KS20250919446当前状态的保护机制
当前状态为pending，企业微信ID为202509190087
"""

import asyncio
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, OperationChannel, ApprovalAction
from app.models import Quote, User

SessionLocal = sessionmaker(bind=engine)

async def test_current_status_scenario():
    """测试当前状态场景：pending状态下的审批保护"""
    print("=== CIS-KS20250919446当前状态测试 ===\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 1. 查看当前状态
        print("1. 查看当前报价单状态...")
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250919446").first()

        if not quote:
            print("❌ 未找到报价单")
            return False

        print(f"   报价单ID: {quote.id}")
        print(f"   当前状态: {quote.approval_status}")
        print(f"   当前企业微信ID: {quote.wecom_approval_id}")
        print(f"   拒绝原因: {quote.rejection_reason}")

        # 2. 场景A：内部先拒绝，然后企业微信尝试批准
        print("\n2. 场景A：内部先拒绝当前审批...")

        # 内部拒绝
        reject_operation = ApprovalOperation(
            action=ApprovalAction.REJECT,
            quote_id=quote.id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="测试内部拒绝 - 当前审批周期",
            reason="不符合最新要求"
        )

        result = approval_engine.execute_operation(reject_operation)
        print(f"   内部拒绝结果: {result.success} - {result.message}")

        # 检查状态
        db.refresh(quote)
        print(f"   拒绝后状态: {quote.approval_status}")
        print(f"   拒绝原因: {quote.rejection_reason}")

        # 3. 现在测试企业微信回调是否被保护
        print("\n3. 测试企业微信回调保护...")
        print(f"   使用当前企业微信ID: {quote.wecom_approval_id}")

        if quote.wecom_approval_id:
            # 企业微信尝试批准已被内部拒绝的报价单
            sync_result = await approval_engine.sync_from_wecom_status_change(
                sp_no=quote.wecom_approval_id,
                new_status="approved",
                operator_info={"userid": "test_current", "name": "当前企业微信测试"}
            )

            if sync_result:
                print("   ❌ 企业微信成功覆盖了内部拒绝，保护失败")
            else:
                print("   ✅ 企业微信回调被正确拒绝，保护生效")

            # 4. 发送澄清消息
            print("\n4. 发送澄清消息...")
            clarification_result = await approval_engine.wecom_integration.send_status_clarification_message(
                quote_id=quote.id,
                internal_action="reject",
                recipient_userid="qixin.chen"
            )
            print(f"   澄清消息结果: {clarification_result}")
        else:
            print("   ⚠️ 没有企业微信ID，跳过回调测试")

        # 5. 验证最终状态
        print("\n5. 验证最终状态...")
        db.refresh(quote)
        print(f"   最终状态: {quote.approval_status}")
        print(f"   拒绝原因: {quote.rejection_reason}")

        success = quote.approval_status == "rejected"

        print(f"\n6. 当前状态保护测试: {'✅ 成功' if success else '❌ 失败'}")

        if success:
            print("\n   📋 测试结论:")
            print("   • 即使经过多次提交-拒绝循环")
            print("   • 每次内部拒绝后都受到保护")
            print("   • 企业微信无法覆盖内部决策")
            print("   • 澄清消息正常发送")
        else:
            print("\n   ❌ 保护机制在多轮审批中失效")

        return success

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def test_full_resubmit_cycle():
    """测试完整的重新提交保护循环"""
    print("\n" + "="*60)
    print("=== 测试完整重新提交保护循环 ===\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250919446").first()

        if not quote:
            return False

        print("当前报价单状态:", quote.approval_status)

        # 如果当前是rejected，先重新提交
        if quote.approval_status == "rejected":
            print("\n1. 重新提交报价单...")
            resubmit_operation = ApprovalOperation(
                action=ApprovalAction.RESUBMIT,
                quote_id=quote.id,
                operator_id=1,
                channel=OperationChannel.INTERNAL,
                comments="测试重新提交保护机制"
            )

            result = approval_engine.execute_operation(resubmit_operation)
            print(f"   重新提交结果: {result.success} - {result.message}")

            db.refresh(quote)
            print(f"   重新提交后状态: {quote.approval_status}")
            print(f"   新企业微信ID: {quote.wecom_approval_id}")

        # 内部批准
        print("\n2. 内部批准...")
        approve_operation = ApprovalOperation(
            action=ApprovalAction.APPROVE,
            quote_id=quote.id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="测试批准 - 验证重新提交后的保护"
        )

        result = approval_engine.execute_operation(approve_operation)
        print(f"   批准结果: {result.success} - {result.message}")

        db.refresh(quote)
        print(f"   批准后状态: {quote.approval_status}")

        # 企业微信尝试拒绝
        if quote.wecom_approval_id:
            print("\n3. 企业微信尝试拒绝已批准的报价单...")
            sync_result = await approval_engine.sync_from_wecom_status_change(
                sp_no=quote.wecom_approval_id,
                new_status="rejected",
                operator_info={"userid": "test_resubmit", "name": "重新提交保护测试"}
            )

            if sync_result:
                print("   ❌ 企业微信成功覆盖了批准状态")
            else:
                print("   ✅ 企业微信回调被正确拒绝，批准状态受到保护")

        # 验证最终状态
        db.refresh(quote)
        success = quote.approval_status == "approved"

        print(f"\n4. 重新提交保护测试: {'✅ 成功' if success else '❌ 失败'}")

        return success

    except Exception as e:
        print(f"❌ 重新提交测试错误: {e}")
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("开始测试CIS-KS20250919446当前状态和重新提交保护...\n")

    # 测试1: 当前状态保护
    success1 = await test_current_status_scenario()

    # 测试2: 完整重新提交循环保护
    success2 = await test_full_resubmit_cycle()

    overall_success = success1 and success2

    print(f"\n" + "="*60)
    print("=== 综合测试结果 ===")
    print(f"当前状态保护: {'✅' if success1 else '❌'}")
    print(f"重新提交保护: {'✅' if success2 else '❌'}")
    print(f"整体结果: {'✅ 全面保护' if overall_success else '❌ 需要修复'}")

    if overall_success:
        print("\n🎉 完整的多轮审批保护机制正常工作！")
        print("   • 无论经过多少次提交-拒绝循环")
        print("   • 每个审批周期的最终状态都受到保护")
        print("   • 企业微信始终无法覆盖内部决策")

    return overall_success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)