#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_db
from app.models import Quote
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

def reset_and_test_quote():
    """重置报价单状态并测试企业微信审批"""
    print("🔧 重置报价单状态并测试企业微信审批")
    print("=" * 60)

    db = next(get_db())

    try:
        # 使用报价单 CIS-KS20250918001
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918001").first()
        if not quote:
            print("❌ 找不到报价单 CIS-KS20250918001")
            return False

        print(f"📋 测试报价单: {quote.quote_number} (ID: {quote.id})")
        print(f"📊 当前状态: status={quote.status}, approval_status={quote.approval_status}")

        # 1. 重置报价单状态为草稿
        print("\n🔄 重置报价单状态为草稿")
        quote.status = 'draft'
        quote.approval_status = 'not_submitted'
        quote.wecom_approval_id = None
        db.commit()
        db.refresh(quote)

        print(f"✅ 重置完成: status={quote.status}, approval_status={quote.approval_status}")

        # 2. 创建审批引擎并提交到企业微信
        engine = UnifiedApprovalEngine(db)

        print("\n🚀 提交审批到企业微信")

        # 创建提交操作
        submit_operation = ApprovalOperation(
            quote_id=quote.id,
            action=ApprovalAction.SUBMIT,
            operator_id=quote.created_by,
            channel=OperationChannel.API,
            comments="测试企业微信审批通知功能"
        )

        # 执行提交操作
        submit_result = engine.execute_operation(submit_operation)

        print(f"📊 提交结果:")
        print(f"   success: {submit_result.success}")
        print(f"   message: {submit_result.message}")
        print(f"   new_status: {submit_result.new_status}")
        print(f"   operation_id: {submit_result.operation_id}")

        if submit_result.success:
            # 刷新报价单状态
            db.refresh(quote)
            print(f"\n✅ 提交成功！数据库状态:")
            print(f"   status: {quote.status}")
            print(f"   approval_status: {quote.approval_status}")
            print(f"   wecom_approval_id: {quote.wecom_approval_id}")

            # 检查是否使用了企业微信
            if quote.wecom_approval_id:
                print("🎉 企业微信审批提交成功！应该能收到通知")
                return True
            else:
                print("⚠️  使用了内部审批系统，未使用企业微信")
                return False
        else:
            print(f"❌ 提交失败: {submit_result.message}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 开始重置并测试企业微信审批通知")

    success = reset_and_test_quote()

    print(f"\n🎯 最终测试结果: {'成功' if success else '失败'}")

    if success:
        print("\n🎉 企业微信审批通知功能已修复并测试成功！")
        print("✅ 配置正确加载")
        print("✅ 企业微信审批提交成功")
        print("✅ 应该能收到企业微信审批通知")
    else:
        print("\n❌ 企业微信审批通知功能仍有问题，需要进一步排查")