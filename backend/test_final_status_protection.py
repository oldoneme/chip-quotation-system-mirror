#!/usr/bin/env python3
"""
测试最终状态保护功能
验证已批准/拒绝的报价单不能被重复操作
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

async def test_final_status_protection():
    """测试最终状态保护功能"""
    print("=== 最终状态保护功能测试 ===\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 1. 创建测试报价单
        print("1. 创建测试报价单...")
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        new_quote = Quote(
            quote_number=f"PROTECTION-TEST-{timestamp}-{unique_id}",
            title="最终状态保护测试",
            customer_name="测试客户",
            customer_contact="测试联系人",
            total_amount=30000.00,
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
            comments="最终状态保护测试提交"
        )

        result = approval_engine.execute_operation(submit_operation)
        print(f"   提交结果: {result.success} - {result.message}")

        # 3. 批准报价单
        print("\n3. 批准报价单...")
        approve_operation = ApprovalOperation(
            action=ApprovalAction.APPROVE,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="测试批准"
        )

        result = approval_engine.execute_operation(approve_operation)
        print(f"   批准结果: {result.success} - {result.message}")

        # 检查状态
        db.refresh(new_quote)
        print(f"   当前状态: {new_quote.approval_status}")

        # 4. 尝试重复批准 - 应该失败
        print("\n4. 尝试重复批准（应该失败）...")
        try:
            result = approval_engine.execute_operation(approve_operation)
            print(f"   ❌ 重复批准成功了，这是个bug: {result}")
        except ValueError as e:
            print(f"   ✅ 重复批准被正确拒绝: {e}")

        # 5. 尝试拒绝已批准的报价单 - 应该失败
        print("\n5. 尝试拒绝已批准的报价单（应该失败）...")
        reject_operation = ApprovalOperation(
            action=ApprovalAction.REJECT,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="尝试拒绝已批准的报价单",
            reason="测试拒绝"
        )

        try:
            result = approval_engine.execute_operation(reject_operation)
            print(f"   ❌ 拒绝已批准报价单成功了，这是个bug: {result}")
        except ValueError as e:
            print(f"   ✅ 拒绝已批准报价单被正确拒绝: {e}")

        # 6. 测试企业微信回调保护
        print("\n6. 测试企业微信回调保护...")

        # 模拟企业微信试图拒绝已批准的报价单
        test_sp_no = f"TEST-SP-{timestamp}"
        new_quote.wecom_approval_id = test_sp_no
        db.commit()

        sync_result = await approval_engine.sync_from_wecom_status_change(
            sp_no=test_sp_no,
            new_status="rejected",
            operator_info={"userid": "test_wecom_user", "name": "测试企业微信用户"}
        )

        if sync_result:
            print("   ❌ 企业微信回调修改已批准报价单成功了，这是个bug")
        else:
            print("   ✅ 企业微信回调被正确拒绝，最终状态得到保护")

        # 7. 验证数据完整性
        print("\n7. 验证数据完整性...")
        db.refresh(new_quote)
        print(f"   最终状态: {new_quote.approval_status}")
        print(f"   审批时间: {new_quote.approved_at}")
        print(f"   审批人: {new_quote.approved_by}")

        # 检查状态是否仍然是批准状态
        if new_quote.approval_status == "approved":
            print("   ✅ 报价单状态保持为已批准，数据完整性正确")
            return True
        else:
            print(f"   ❌ 报价单状态被意外修改为: {new_quote.approval_status}")
            return False

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("启动最终状态保护功能测试...\n")

    success = await test_final_status_protection()

    print(f"\n=== 测试完成 ===")
    print(f"结果: {'✅ 通过' if success else '❌ 失败'}")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)