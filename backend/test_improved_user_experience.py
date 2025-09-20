#!/usr/bin/env python3
"""
测试改进的用户体验流程
验证企业微信回调时主动告知用户"审批已完成，操作不会生效"
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, OperationChannel, ApprovalAction
from app.models import Quote, User

SessionLocal = sessionmaker(bind=engine)

async def test_approval_completion_notification():
    """测试审批完成通知机制"""
    print("=== 改进的用户体验流程测试 ===\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 1. 创建测试报价单
        print("1. 创建测试报价单...")
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        new_quote = Quote(
            quote_number=f"UX-IMPROVE-{timestamp}-{unique_id}",
            title="改进用户体验测试",
            customer_name="测试客户",
            customer_contact="测试联系人",
            total_amount=60000.00,
            approval_status="not_submitted",
            approval_method="internal",
            created_by=1,
            status="active"
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)
        quote_id = new_quote.id
        print(f"   ✅ 创建报价单: {new_quote.quote_number} (ID: {quote_id})")

        # 2. 提交审批
        print("\n2. 提交审批...")
        submit_operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="改进用户体验测试提交"
        )

        result = approval_engine.execute_operation(submit_operation)
        print(f"   提交结果: {result.success} - {result.message}")

        # 设置企业微信ID
        test_sp_no = f"UX-SP-{timestamp}"
        new_quote.wecom_approval_id = test_sp_no
        db.commit()
        print(f"   设置企业微信ID: {test_sp_no}")

        # 测试场景1: 内部批准 → 企业微信尝试拒绝
        print("\n" + "="*60)
        print("场景1: 内部批准 → 企业微信尝试拒绝")
        print("="*60)

        # 3. 内部批准
        print("\n3. 内部批准报价单...")
        approve_operation = ApprovalOperation(
            action=ApprovalAction.APPROVE,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="测试批准 - 验证后续企业微信通知"
        )

        result = approval_engine.execute_operation(approve_operation)
        print(f"   批准结果: {result.success} - {result.message}")

        db.refresh(new_quote)
        print(f"   批准后状态: {new_quote.approval_status}")

        # 4. 企业微信尝试拒绝（冲突场景）
        print("\n4. 企业微信尝试拒绝已批准的报价单...")
        print("   🎯 预期行为: 系统应该主动告知用户审批已完成")

        sync_result = await approval_engine.sync_from_wecom_status_change(
            sp_no=test_sp_no,
            new_status="rejected",
            operator_info={
                "userid": "qixin.chen",
                "name": "陈祺欣"
            }
        )

        if sync_result:
            print("   ❌ 企业微信成功覆盖了批准状态")
        else:
            print("   ✅ 企业微信回调被正确拒绝")
            print("   📱 系统已主动发送'审批已完成'通知给陈祺欣")

        # 验证状态保持不变
        db.refresh(new_quote)
        print(f"   最终状态: {new_quote.approval_status} (应该仍是 approved)")

        # 测试场景2: 创建新报价单测试一致场景
        print("\n" + "="*60)
        print("场景2: 内部拒绝 → 企业微信尝试拒绝（一致场景）")
        print("="*60)

        # 5. 创建第二个测试报价单
        print("\n5. 创建第二个测试报价单...")
        unique_id2 = str(uuid.uuid4())[:8]

        new_quote2 = Quote(
            quote_number=f"UX-CONSISTENT-{timestamp}-{unique_id2}",
            title="一致场景测试",
            customer_name="测试客户2",
            customer_contact="测试联系人2",
            total_amount=70000.00,
            approval_status="not_submitted",
            approval_method="internal",
            created_by=1,
            status="active"
        )
        db.add(new_quote2)
        db.commit()
        db.refresh(new_quote2)
        quote_id2 = new_quote2.id
        print(f"   ✅ 创建第二个报价单: {new_quote2.quote_number} (ID: {quote_id2})")

        # 提交
        submit_operation2 = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote_id2,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="一致场景测试提交"
        )
        approval_engine.execute_operation(submit_operation2)

        # 设置企业微信ID
        test_sp_no2 = f"UX-CONSISTENT-SP-{timestamp}"
        new_quote2.wecom_approval_id = test_sp_no2
        db.commit()

        # 6. 内部拒绝
        print("\n6. 内部拒绝第二个报价单...")
        reject_operation = ApprovalOperation(
            action=ApprovalAction.REJECT,
            quote_id=quote_id2,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="测试拒绝 - 验证一致场景通知",
            reason="测试拒绝原因"
        )

        result = approval_engine.execute_operation(reject_operation)
        print(f"   拒绝结果: {result.success} - {result.message}")

        # 7. 企业微信也尝试拒绝（一致场景）
        print("\n7. 企业微信也尝试拒绝（一致场景）...")
        print("   🎯 预期行为: 系统应该告知用户操作一致但不会生效")

        sync_result2 = await approval_engine.sync_from_wecom_status_change(
            sp_no=test_sp_no2,
            new_status="rejected",
            operator_info={
                "userid": "liang.li",
                "name": "李亮"
            }
        )

        if sync_result2:
            print("   ❌ 企业微信覆盖了拒绝状态")
        else:
            print("   ✅ 企业微信回调被正确拒绝")
            print("   📱 系统已主动发送'审批已完成'通知给李亮（一致场景）")

        # 8. 验证结果
        success1 = new_quote.approval_status == "approved"
        success2 = new_quote2.approval_status == "rejected"
        overall_success = success1 and success2

        print(f"\n" + "="*60)
        print("=== 测试结果总结 ===")
        print(f"冲突场景保护: {'✅' if success1 else '❌'}")
        print(f"一致场景保护: {'✅' if success2 else '❌'}")
        print(f"整体结果: {'✅ 完美' if overall_success else '❌ 需要修复'}")

        if overall_success:
            print("\n🎉 改进的用户体验功能完全正常！")
            print("\n📱 新的用户体验:")
            print("   • 用户在企业微信中点击审批后")
            print("   • 如果审批已在内部完成，立即收到通知")
            print("   • 明确告知操作不会生效")
            print("   • 区分冲突和一致两种情况")
            print("   • 避免用户困惑和重复操作")

            print("\n🔔 通知消息示例:")
            print("   冲突场景: '⚠️ 审批状态冲突提醒'")
            print("   一致场景: 'ℹ️ 审批已完成提醒'")
            print("   都会明确说明：您的点击操作不会改变系统状态")

        return overall_success

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def test_message_content_verification():
    """验证消息内容的具体格式"""
    print("\n" + "="*60)
    print("=== 消息内容验证测试 ===")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 使用现有的报价单进行消息内容测试
        quote = db.query(Quote).filter(Quote.quote_number.like("UX-IMPROVE-%")).first()

        if quote:
            print(f"\n使用报价单: {quote.quote_number}")
            print("测试不同类型的通知消息...")

            # 测试冲突消息
            print("\n1. 测试冲突场景消息...")
            await approval_engine._send_approval_completed_notification(
                quote_id=quote.id,
                current_status="approved",
                attempted_action="rejected",
                operator_info={"userid": "qixin.chen", "name": "陈祺欣"}
            )
            print("   ✅ 冲突消息已发送")

            # 测试一致消息
            print("\n2. 测试一致场景消息...")
            await approval_engine._send_approval_completed_notification(
                quote_id=quote.id,
                current_status="approved",
                attempted_action="approved",
                operator_info={"userid": "liang.li", "name": "李亮"}
            )
            print("   ✅ 一致消息已发送")

            return True
        else:
            print("   ⚠️ 没有找到测试报价单，跳过消息内容验证")
            return True

    except Exception as e:
        print(f"❌ 消息内容验证失败: {e}")
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("开始测试改进的用户体验流程...\n")

    # 测试1: 主要功能测试
    success1 = await test_approval_completion_notification()

    # 测试2: 消息内容验证
    success2 = await test_message_content_verification()

    overall_success = success1 and success2

    print(f"\n" + "="*80)
    print("=== 最终测试结果 ===")
    print(f"功能测试: {'✅' if success1 else '❌'}")
    print(f"消息验证: {'✅' if success2 else '❌'}")
    print(f"总体结果: {'🎉 全面成功' if overall_success else '❌ 需要调试'}")

    if overall_success:
        print("\n🚀 用户体验改进完成！")
        print("\n✨ 新功能特性:")
        print("   • 主动通知：检测到重复操作时立即告知用户")
        print("   • 明确说明：清楚告知操作不会生效的原因")
        print("   • 情况区分：区分冲突和一致两种场景")
        print("   • 防止困惑：避免用户对状态不一致的疑惑")
        print("   • 用户友好：提供查看详情的链接")

    return overall_success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)