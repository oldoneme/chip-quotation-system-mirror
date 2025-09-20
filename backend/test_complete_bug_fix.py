#!/usr/bin/env python3
"""
完整Bug修复验证
重现CIS-KS20250919006的问题场景并验证修复
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
import sqlite3

SessionLocal = sessionmaker(bind=engine)

async def test_complete_bug_fix():
    """测试完整的bug修复 - 重现并验证修复"""
    print("=== 完整Bug修复验证测试 ===")
    print("重现场景: 内部批准 -> 企业微信回调拒绝 -> 验证保护\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 1. 创建测试报价单（模拟CIS-KS20250919006场景）
        print("1. 创建测试报价单（模拟真实场景）...")
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        new_quote = Quote(
            quote_number=f"CIS-KS{timestamp}",
            title="Bug修复验证测试",
            customer_name="测试客户",
            customer_contact="测试联系人",
            total_amount=25000.00,
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

        # 2. 提交审批（触发企业微信审批）
        print("\n2. 提交审批（会创建企业微信审批）...")
        submit_operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="完整流程测试提交"
        )

        result = approval_engine.execute_operation(submit_operation)
        print(f"   提交结果: {result.success} - {result.message}")

        # 检查提交后状态
        db.refresh(new_quote)
        print(f"   提交后状态: {new_quote.approval_status}")
        print(f"   审批方法: {new_quote.approval_method}")
        print(f"   企业微信ID: {new_quote.wecom_approval_id}")

        # 3. 内部批准（这里会发生状态变化）
        print("\n3. 内部批准操作...")
        approve_operation = ApprovalOperation(
            action=ApprovalAction.APPROVE,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="内部批准测试"
        )

        result = approval_engine.execute_operation(approve_operation)
        print(f"   批准结果: {result.success} - {result.message}")

        # 检查批准后状态
        db.refresh(new_quote)
        print(f"   批准后状态: {new_quote.approval_status}")
        print(f"   批准时间: {new_quote.approved_at}")
        print(f"   批准人: {new_quote.approved_by}")

        # 4. 模拟企业微信回调尝试拒绝（这是bug发生的地方）
        print("\n4. 模拟企业微信回调尝试拒绝已批准报价单...")

        if new_quote.wecom_approval_id:
            print(f"   使用企业微信ID: {new_quote.wecom_approval_id}")

            # 尝试通过企业微信回调拒绝已批准的报价单
            sync_result = await approval_engine.sync_from_wecom_status_change(
                sp_no=new_quote.wecom_approval_id,
                new_status="rejected",
                operator_info={
                    "userid": "test_approver",
                    "name": "测试审批人"
                }
            )

            print(f"   回调同步结果: {sync_result}")

            if sync_result:
                print("   ❌ 企业微信成功覆盖了内部批准，这是原来的bug行为")
            else:
                print("   ✅ 企业微信回调被正确拒绝，bug已修复")

        # 5. 最终状态验证
        print("\n5. 最终状态验证...")
        db.refresh(new_quote)

        print(f"   最终审批状态: {new_quote.approval_status}")
        print(f"   最终主状态: {new_quote.status}")
        print(f"   批准时间: {new_quote.approved_at}")
        print(f"   拒绝原因: {new_quote.rejection_reason}")

        # 6. 审批历史一致性检查
        print("\n6. 审批历史一致性检查...")

        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()

        cursor.execute('SELECT action, status, created_at, comments FROM approval_records WHERE quote_id = ? ORDER BY created_at ASC', (quote_id,))
        records = cursor.fetchall()

        print(f"   审批记录数量: {len(records)}")
        for i, record in enumerate(records, 1):
            action, record_status, created_at, comments = record
            print(f"   记录{i}: {action} -> {record_status} ({created_at[:19]})")
            print(f"           备注: {comments[:50]}...")

        conn.close()

        # 7. 判断修复是否成功
        success = (
            new_quote.approval_status == "approved" and  # 状态应该保持已批准
            new_quote.approved_at is not None and       # 应该有批准时间
            new_quote.rejection_reason is None          # 不应该有拒绝原因
        )

        print(f"\n7. Bug修复结果: {'✅ 成功' if success else '❌ 失败'}")

        if success:
            print("   🎉 企业微信回调无法覆盖内部批准结果")
            print("   🎉 最终状态保护机制正常工作")
            print("   🎉 数据一致性得到保障")
        else:
            print("   ❌ 企业微信仍然可以覆盖内部批准")
            print("   ❌ 需要进一步检查保护机制")

        return success

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("启动完整Bug修复验证测试...\n")

    success = await test_complete_bug_fix()

    print(f"\n=== 测试完成 ===")
    print(f"Bug修复状态: {'✅ 完全修复' if success else '❌ 仍有问题'}")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)