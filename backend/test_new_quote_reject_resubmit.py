#!/usr/bin/env python3
"""
测试新报价单的完整流程：创建 -> 提交审批 -> 拒绝 -> 重新提交审批
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel
from app.models import Quote, QuoteItem

def create_test_quote(db: Session) -> Quote:
    """创建测试报价单"""
    print("📝 创建新的测试报价单...")

    # 生成报价单编号
    quote_number = f"CIS-KS{datetime.now().strftime('%Y%m%d%H%M')}"

    # 创建报价单
    quote = Quote(
        quote_number=quote_number,
        title="测试报价单-拒绝重提交流程",
        customer_name="测试客户-拒绝重提交",
        customer_contact="测试联系人",
        customer_phone="13800138000",
        customer_email="test@example.com",
        total_amount=1000.00,
        status="draft",
        approval_status="not_submitted",
        created_by=1,
        created_at=datetime.utcnow()
    )

    db.add(quote)
    db.flush()  # 获取ID

    # 添加报价项目
    quote_item = QuoteItem(
        quote_id=quote.id,
        item_name="测试项目",
        item_description="用于测试拒绝重新提交流程",
        quantity=1,
        unit_price=1000.00,
        total_price=1000.00
    )

    db.add(quote_item)
    db.commit()

    print(f"✅ 创建成功：{quote.quote_number} (ID: {quote.id})")
    return quote

def test_full_reject_resubmit_flow():
    """测试完整的拒绝重新提交流程"""
    print("🔍 测试完整的拒绝重新提交流程")

    # 获取数据库连接
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # 步骤1: 创建新报价单
        quote = create_test_quote(db)

        # 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 步骤2: 首次提交审批
        print(f"\n🚀 步骤2: 首次提交审批...")
        operation1 = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote.id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            reason="首次提交审批测试"
        )

        result1 = engine.execute_operation(operation1)
        print(f"首次提交结果: 成功={result1.success}, 消息={result1.message}")

        # 刷新报价单状态
        db.refresh(quote)
        print(f"首次提交后状态: {quote.status}, 审批状态: {quote.approval_status}")

        # 步骤3: 模拟拒绝
        print(f"\n❌ 步骤3: 模拟拒绝审批...")
        operation2 = ApprovalOperation(
            action=ApprovalAction.REJECT,
            quote_id=quote.id,
            operator_id=2,  # 不同的操作员
            channel=OperationChannel.INTERNAL,
            reason="测试拒绝，用于验证重新提交流程"
        )

        result2 = engine.execute_operation(operation2)
        print(f"拒绝结果: 成功={result2.success}, 消息={result2.message}")

        # 刷新报价单状态
        db.refresh(quote)
        print(f"拒绝后状态: {quote.status}, 审批状态: {quote.approval_status}")

        # 步骤4: 重新提交审批
        print(f"\n🔄 步骤4: 重新提交审批...")
        operation3 = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote.id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            reason="被拒绝后重新提交审批"
        )

        result3 = engine.execute_operation(operation3)
        print(f"重新提交结果: 成功={result3.success}, 消息={result3.message}")

        # 刷新报价单状态
        db.refresh(quote)
        print(f"重新提交后状态: {quote.status}, 审批状态: {quote.approval_status}")
        print(f"企业微信审批ID: {quote.wecom_approval_id}")

        # 查看审批记录
        print(f"\n📜 审批记录历史:")
        import sqlite3
        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ar.action, ar.status, ar.wecom_sp_no, ar.created_at, ar.comments
            FROM approval_records ar
            WHERE ar.quote_id = ?
            ORDER BY ar.created_at ASC
        ''', (quote.id,))
        records = cursor.fetchall()
        for i, record in enumerate(records, 1):
            print(f"   {i}. 动作: {record[0]}, 状态: {record[1]}, 企业微信编号: {record[2]}, 时间: {record[3]}, 备注: {record[4]}")
        conn.close()

        return quote.quote_number

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        db.close()

if __name__ == "__main__":
    quote_number = test_full_reject_resubmit_flow()
    if quote_number:
        print(f"\n🎉 测试完成！报价单号: {quote_number}")
        print(f"💡 现在可以检查企业微信是否收到重新提交的审批通知")
    else:
        print(f"\n❌ 测试失败")