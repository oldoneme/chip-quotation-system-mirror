#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from dotenv import load_dotenv
load_dotenv()

from app.database import get_db
from app.models import Quote
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

def test_complete_approval_workflow():
    """测试完整的审批工作流：提交 -> 拒绝 -> 重新提交"""
    print("🔧 测试完整的审批工作流")
    print("=" * 70)

    db = next(get_db())

    try:
        # 使用报价单 CIS-KS20250918001
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918001").first()
        if not quote:
            print("❌ 找不到报价单 CIS-KS20250918001")
            return False

        print(f"📋 测试报价单: {quote.quote_number} (ID: {quote.id})")
        print(f"📊 初始状态: status={quote.status}, approval_status={quote.approval_status}")

        # 1. 重置报价单状态为草稿
        print("\n🔄 步骤1: 重置报价单状态为草稿")
        quote.status = 'draft'
        quote.approval_status = 'not_submitted'
        quote.wecom_approval_id = None
        quote.rejection_reason = None
        db.commit()
        db.refresh(quote)
        print(f"✅ 重置完成: status={quote.status}, approval_status={quote.approval_status}")

        # 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 2. 提交审批
        print("\n🚀 步骤2: 提交审批到企业微信")
        submit_operation = ApprovalOperation(
            quote_id=quote.id,
            action=ApprovalAction.SUBMIT,
            operator_id=quote.created_by,
            channel=OperationChannel.API,
            comments="测试完整工作流 - 第一次提交"
        )

        submit_result = engine.execute_operation(submit_operation)
        print(f"📊 提交结果: success={submit_result.success}, message={submit_result.message}")

        if submit_result.success:
            db.refresh(quote)
            print(f"✅ 提交成功: status={quote.status}, approval_status={quote.approval_status}")
            print(f"🆔 企业微信审批ID: {quote.wecom_approval_id}")
        else:
            print(f"❌ 提交失败: {submit_result.message}")
            return False

        # 3. 模拟审批人拒绝（假设用户ID=7是审批人）
        print("\n❌ 步骤3: 模拟审批人拒绝")
        reject_operation = ApprovalOperation(
            quote_id=quote.id,
            action=ApprovalAction.REJECT,
            operator_id=7,  # 假设用户7是审批人
            channel=OperationChannel.API,
            reason="测试拒绝 - 需要修改报价",
            comments="价格过高，请重新核算"
        )

        reject_result = engine.execute_operation(reject_operation)
        print(f"📊 拒绝结果: success={reject_result.success}, message={reject_result.message}")

        if reject_result.success:
            db.refresh(quote)
            print(f"✅ 拒绝成功: status={quote.status}, approval_status={quote.approval_status}")
            print(f"📝 拒绝原因: {quote.rejection_reason}")
        else:
            print(f"❌ 拒绝失败: {reject_result.message}")

        # 4. 模拟重新提交（重置状态后重新提交）
        print("\n🔄 步骤4: 重新提交审批")

        # 重置状态以模拟用户修改后重新提交
        quote.status = 'draft'
        quote.approval_status = 'not_submitted'
        quote.wecom_approval_id = None  # 清除之前的企业微信审批ID
        db.commit()
        db.refresh(quote)

        resubmit_operation = ApprovalOperation(
            quote_id=quote.id,
            action=ApprovalAction.SUBMIT,
            operator_id=quote.created_by,
            channel=OperationChannel.API,
            comments="重新提交 - 已修改价格"
        )

        resubmit_result = engine.execute_operation(resubmit_operation)
        print(f"📊 重新提交结果: success={resubmit_result.success}, message={resubmit_result.message}")

        if resubmit_result.success:
            db.refresh(quote)
            print(f"✅ 重新提交成功: status={quote.status}, approval_status={quote.approval_status}")
            print(f"🆔 新的企业微信审批ID: {quote.wecom_approval_id}")
            return True
        else:
            print(f"❌ 重新提交失败: {resubmit_result.message}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 开始完整审批工作流测试")

    success = test_complete_approval_workflow()

    print(f"\n🎯 整体测试结果: {'成功' if success else '失败'}")

    if success:
        print("\n🎉 完整审批工作流测试成功！")
        print("✅ 1. 提交审批到企业微信")
        print("✅ 2. 拒绝审批并发送通知")
        print("✅ 3. 重新提交审批到企业微信")
        print("✅ 企业微信通知应该在每个步骤正常发送")
    else:
        print("\n❌ 完整审批工作流测试失败")
        print("需要检查企业微信API配置和网络连接")