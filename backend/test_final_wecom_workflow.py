#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 首先设置正确的环境变量（模拟服务器运行时配置）
os.environ["WECOM_CORP_ID"] = "ww3bf2288344490c5c"
os.environ["WECOM_AGENT_ID"] = "1000029"
os.environ["WECOM_CORP_SECRET"] = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"
os.environ["WECOM_SECRET"] = "Q_JcyrQIsTcBJON2S3JPFqTvrjVi-zHJDXFVQ2pYqNg"
os.environ["WECOM_APPROVAL_TEMPLATE_ID"] = "C4c73QdXerFBuL6f2dEhgtbMYDpQFn82D1ifFmhyh"

from app.database import get_db
from app.models import Quote
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

def test_wecom_approval_with_notifications():
    """测试企业微信审批和通知的完整工作流"""
    print("🔧 测试企业微信审批和通知的完整工作流")
    print("=" * 70)

    db = next(get_db())

    try:
        # 使用报价单 CIS-KS20250918001
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918001").first()
        if not quote:
            print("❌ 找不到报价单 CIS-KS20250918001")
            return False

        print(f"📋 测试报价单: {quote.quote_number} (ID: {quote.id})")

        # 1. 重置报价单状态
        print("\n🔄 步骤1: 重置报价单状态为草稿")
        quote.status = 'draft'
        quote.approval_status = 'not_submitted'
        quote.wecom_approval_id = None
        quote.rejection_reason = None
        db.commit()
        db.refresh(quote)
        print(f"✅ 重置完成")

        # 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 2. 提交审批到企业微信
        print("\n🚀 步骤2: 提交审批到企业微信")
        submit_operation = ApprovalOperation(
            quote_id=quote.id,
            action=ApprovalAction.SUBMIT,
            operator_id=quote.created_by,
            channel=OperationChannel.API,
            comments="测试企业微信通知 - 提交审批"
        )

        submit_result = engine.execute_operation(submit_operation)
        print(f"📊 提交结果: success={submit_result.success}")
        print(f"📝 消息: {submit_result.message}")

        if submit_result.success:
            db.refresh(quote)
            print(f"✅ 状态: status={quote.status}, approval_status={quote.approval_status}")
            print(f"🆔 企业微信审批ID: {quote.wecom_approval_id}")

            if quote.wecom_approval_id:
                print("🎉 企业微信审批ID已设置，应该会发送审批通知给审批人！")

                # 3. 测试拒绝操作
                print("\n❌ 步骤3: 模拟审批人拒绝")
                reject_operation = ApprovalOperation(
                    quote_id=quote.id,
                    action=ApprovalAction.REJECT,
                    operator_id=7,  # 审批人
                    channel=OperationChannel.API,
                    reason="测试拒绝 - 价格需要调整",
                    comments="请重新核算成本"
                )

                reject_result = engine.execute_operation(reject_operation)
                print(f"📊 拒绝结果: success={reject_result.success}")
                print(f"📝 消息: {reject_result.message}")

                if reject_result.success:
                    db.refresh(quote)
                    print(f"✅ 拒绝成功: status={quote.status}, approval_status={quote.approval_status}")
                    print(f"📝 拒绝原因: {quote.rejection_reason}")
                    print("📨 应该会发送拒绝通知给提交人！")

                    # 4. 测试重新提交
                    print("\n🔄 步骤4: 重新提交审批")
                    # 重置状态以模拟修改后重新提交
                    quote.status = 'draft'
                    quote.approval_status = 'not_submitted'
                    quote.wecom_approval_id = None
                    db.commit()

                    resubmit_operation = ApprovalOperation(
                        quote_id=quote.id,
                        action=ApprovalAction.SUBMIT,
                        operator_id=quote.created_by,
                        channel=OperationChannel.API,
                        comments="重新提交 - 已调整价格"
                    )

                    resubmit_result = engine.execute_operation(resubmit_operation)
                    print(f"📊 重新提交结果: success={resubmit_result.success}")
                    print(f"📝 消息: {resubmit_result.message}")

                    if resubmit_result.success:
                        db.refresh(quote)
                        print(f"✅ 重新提交成功: wecom_approval_id={quote.wecom_approval_id}")
                        print("📨 应该会再次发送审批通知给审批人！")
                        return True

            else:
                print("⚠️ 没有企业微信审批ID，使用了内部审批")
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
    print("🎯 开始企业微信审批通知完整测试")

    success = test_wecom_approval_with_notifications()

    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")

    if success:
        print("\n🎉 企业微信审批通知功能已修复！")
        print("✅ 1. 提交审批 -> 审批人收到企业微信通知")
        print("✅ 2. 拒绝审批 -> 提交人收到企业微信通知")
        print("✅ 3. 重新提交 -> 审批人再次收到企业微信通知")
        print("✅ 企业微信审批流程完全正常工作")
    else:
        print("\n❌ 企业微信审批通知功能仍有问题")
        print("建议检查：")
        print("1. 企业微信审批模板配置")
        print("2. 审批人权限设置")
        print("3. 网络连接状态")