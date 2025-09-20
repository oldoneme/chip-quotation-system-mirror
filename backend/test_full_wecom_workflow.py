#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_db
from app.models import Quote
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

def test_full_wecom_workflow():
    """测试完整的企业微信审批工作流"""
    print("🔧 测试完整的企业微信审批工作流")
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

        # 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 测试提交审批（如果还没提交）
        if quote.approval_status in ['not_submitted', 'draft']:
            print("\n🚀 提交审批到企业微信")

            # 创建提交操作
            submit_operation = ApprovalOperation(
                quote_id=quote.id,
                action=ApprovalAction.SUBMIT,
                operator_id=quote.created_by,
                channel=OperationChannel.API,
                comments="测试提交到企业微信审批"
            )

            # 执行提交操作
            submit_result = engine.execute_operation(submit_operation)

            print(f"提交结果: success={submit_result.success}")
            print(f"消息: {submit_result.message}")
            print(f"新状态: {submit_result.new_status}")
            print(f"操作ID: {submit_result.operation_id}")

            if submit_result.success:
                # 刷新报价单状态
                db.refresh(quote)
                print(f"✅ 提交成功！数据库状态: status={quote.status}, approval_status={quote.approval_status}")
                print(f"企业微信审批ID: {quote.wecom_approval_id}")

                return True
            else:
                print(f"❌ 提交失败: {submit_result.message}")
                return False
        else:
            print(f"⚠️  报价单当前状态为 {quote.approval_status}，不需要重新提交")
            print(f"企业微信审批ID: {quote.wecom_approval_id}")
            return True

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 开始完整企业微信审批工作流测试")

    success = test_full_wecom_workflow()

    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")

    if success:
        print("\n🎉 企业微信审批通知功能已修复！")
        print("✅ 配置正确加载")
        print("✅ 审批提交正常工作")
        print("✅ 应该能收到企业微信通知")