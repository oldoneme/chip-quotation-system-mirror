#!/usr/bin/env python3
"""
测试企业微信回调最终状态保护
验证企业微信回调不能覆盖已批准的报价单
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

async def test_wecom_callback_protection():
    """测试企业微信回调最终状态保护"""
    print("=== 企业微信回调最终状态保护测试 ===\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 1. 创建测试报价单
        print("1. 创建测试报价单...")
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        new_quote = Quote(
            quote_number=f"CALLBACK-PROTECT-{timestamp}-{unique_id}",
            title="企业微信回调保护测试",
            customer_name="测试客户",
            customer_contact="测试联系人",
            total_amount=40000.00,
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
            comments="企业微信回调保护测试提交"
        )

        result = approval_engine.execute_operation(submit_operation)
        print(f"   提交结果: {result.success} - {result.message}")

        # 3. 内部批准报价单
        print("\n3. 内部批准报价单...")
        approve_operation = ApprovalOperation(
            action=ApprovalAction.APPROVE,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="内部批准测试"
        )

        result = approval_engine.execute_operation(approve_operation)
        print(f"   批准结果: {result.success} - {result.message}")

        # 检查状态
        db.refresh(new_quote)
        print(f"   批准后状态: {new_quote.approval_status}")

        # 4. 设置企业微信ID并测试回调保护
        print("\n4. 模拟企业微信回调尝试覆盖已批准状态...")

        # 为报价单设置企业微信ID
        test_sp_no = f"CALLBACK-TEST-{timestamp}"
        new_quote.wecom_approval_id = test_sp_no
        db.commit()

        print(f"   设置企业微信ID: {test_sp_no}")

        # 尝试通过统一审批引擎模拟企业微信回调
        print("   测试统一审批引擎的回调保护...")
        sync_result = await approval_engine.sync_from_wecom_status_change(
            sp_no=test_sp_no,
            new_status="rejected",
            operator_info={"userid": "callback_test_user", "name": "企业微信回调测试"}
        )

        if sync_result:
            print("   ❌ 企业微信回调成功修改了已批准状态，这是个bug")
        else:
            print("   ✅ 企业微信回调被正确拒绝，最终状态保护生效")

        # 5. 验证状态保持不变
        print("\n5. 验证报价单状态...")
        db.refresh(new_quote)

        print(f"   最终状态: {new_quote.approval_status}")
        print(f"   批准时间: {new_quote.approved_at}")
        print(f"   批准人: {new_quote.approved_by}")

        # 检查状态是否仍然是批准状态
        if new_quote.approval_status == "approved":
            print("   ✅ 报价单状态保持为已批准，企业微信回调保护成功")
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
    print("启动企业微信回调最终状态保护测试...\n")

    success = await test_wecom_callback_protection()

    print(f"\n=== 测试完成 ===")
    print(f"结果: {'✅ 通过' if success else '❌ 失败'}")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)