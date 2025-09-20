#!/usr/bin/env python3
"""
完整统一审批流程测试
验证100%统一审批功能是否正确实现
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
from app.models import Quote, User, ApprovalRecord
import sqlite3

SessionLocal = sessionmaker(bind=engine)

async def test_unified_approval_workflow():
    """测试完整的统一审批流程"""
    print("=== 完整统一审批流程测试 ===\n")

    db = SessionLocal()
    approval_engine = UnifiedApprovalEngine(db)

    try:
        # 1. 创建新报价单进行测试
        print("1. 创建测试报价单...")
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        new_quote = Quote(
            quote_number=f"FINAL-TEST-{timestamp}-{unique_id}",
            title="统一审批最终测试",
            customer_name="测试客户",
            customer_contact="测试联系人",
            total_amount=50000.00,
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

        # 2. 测试提交审批 - 应该触发企业微信审批
        print("\n2. 提交审批...")
        submit_operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            comments="统一审批流程测试提交"
        )

        result = approval_engine.execute_operation(submit_operation)
        print(f"   提交结果: {result}")

        # 检查提交后的状态
        db.refresh(new_quote)
        print(f"   提交后状态: {new_quote.approval_status}")
        print(f"   审批方法: {new_quote.approval_method}")
        print(f"   企业微信ID: {new_quote.wecom_approval_id}")

        # 3. 验证企业微信审批ID是否保存
        if new_quote.wecom_approval_id:
            print("   ✅ 企业微信审批ID已保存")
            if new_quote.approval_method == 'wecom':
                print("   ✅ 审批方法正确标记为wecom")
            else:
                print(f"   ❌ 审批方法错误: {new_quote.approval_method}")
        else:
            print("   ❌ 企业微信审批ID未保存")

        # 4. 测试企业微信回调模拟
        print("\n3. 模拟企业微信审批回调...")
        if new_quote.wecom_approval_id:
            callback_data = {
                "sp_no": new_quote.wecom_approval_id,
                "sp_name": "统一审批测试",
                "sp_status": 2,  # 审批通过
                "template_id": "test_template",
                "approver": {
                    "userid": "test_approver",
                    "name": "测试审批人"
                }
            }

            # 使用统一审批引擎处理回调
            sync_success = await approval_engine.sync_from_wecom_status_change(
                sp_no=new_quote.wecom_approval_id,
                new_status="approved",
                operator_info={"userid": "test_approver", "name": "测试审批人"}
            )

            print(f"   回调同步结果: {sync_success}")

            # 检查同步后状态
            db.refresh(new_quote)
            print(f"   同步后状态: {new_quote.approval_status}")
            print(f"   审批人: {new_quote.approved_by}")
            print(f"   审批时间: {new_quote.approved_at}")

        # 5. 检查审批记录
        print("\n4. 检查审批记录...")
        records = db.query(ApprovalRecord).filter(
            ApprovalRecord.quote_id == quote_id
        ).order_by(ApprovalRecord.created_at.desc()).all()

        print(f"   审批记录数量: {len(records)}")
        for i, record in enumerate(records, 1):
            print(f"   记录{i}: 操作={record.action}, 状态={record.status}, 企业微信SP号={record.wecom_sp_no}")

        # 6. 数据一致性验证
        print("\n5. 数据一致性验证...")

        # 验证企业微信相关字段一致性
        if new_quote.wecom_approval_id:
            wecom_records = [r for r in records if r.wecom_sp_no == new_quote.wecom_approval_id]
            if wecom_records:
                print("   ✅ 审批记录与企业微信ID一致")
            else:
                print("   ❌ 审批记录与企业微信ID不一致")

        # 验证审批状态一致性
        if new_quote.approval_status in ['approved', 'rejected']:
            final_record = records[0] if records else None
            if final_record and final_record.status == new_quote.approval_status:
                print("   ✅ 报价单状态与最新记录一致")
            else:
                print("   ❌ 报价单状态与记录不一致")

        # 7. 统一审批功能评估
        print("\n6. 统一审批功能评估...")

        checks = {
            "企业微信ID保存": new_quote.wecom_approval_id is not None,
            "审批方法正确": new_quote.approval_method == 'wecom' if new_quote.wecom_approval_id else True,
            "状态同步": new_quote.approval_status in ['pending', 'approved', 'rejected'],
            "记录完整": len(records) > 0,
            "双向同步": len([r for r in records if r.wecom_sp_no]) > 0 if new_quote.wecom_approval_id else True
        }

        passed = sum(checks.values())
        total = len(checks)

        print(f"   通过检查: {passed}/{total}")
        for check_name, result in checks.items():
            status = "✅" if result else "❌"
            print(f"   {status} {check_name}")

        # 统一性评分
        unification_score = (passed / total) * 100
        print(f"\n   🎯 统一审批完成度: {unification_score:.1f}%")

        if unification_score == 100:
            print("   🎉 恭喜！已实现100%统一审批功能")
        else:
            print(f"   ⚠️  还需要修复 {100 - unification_score:.1f}% 的问题")

        return unification_score >= 100

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("启动统一审批流程最终测试...\n")

    success = await test_unified_approval_workflow()

    print(f"\n=== 测试完成 ===")
    print(f"结果: {'✅ 通过' if success else '❌ 失败'}")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)