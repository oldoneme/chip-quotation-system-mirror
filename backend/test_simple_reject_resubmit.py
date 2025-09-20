#!/usr/bin/env python3
"""
简化测试：直接通过数据库模拟拒绝状态，然后测试重新提交
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel
from app.models import Quote, QuoteItem
import sqlite3

def create_and_test_resubmit():
    """创建报价单，设置为拒绝状态，然后测试重新提交"""
    print("🔍 测试拒绝后重新提交流程")

    # 直接操作数据库创建报价单和设置状态
    conn = sqlite3.connect('app/test.db')
    cursor = conn.cursor()

    try:
        # 生成报价单编号
        quote_number = f"CIS-KS{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # 创建报价单（直接设置为拒绝状态）
        cursor.execute('''
            INSERT INTO quotes
            (quote_number, title, customer_name, customer_contact, customer_phone, customer_email,
             total_amount, status, approval_status, created_by, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            quote_number,
            "测试报价单-拒绝重提交",
            "测试客户",
            "测试联系人",
            "13800138000",
            "test@example.com",
            1000.00,
            "rejected",  # 直接设置为拒绝状态
            "rejected",
            1,
            datetime.utcnow()
        ))

        quote_id = cursor.lastrowid

        # 添加报价项目
        cursor.execute('''
            INSERT INTO quote_items
            (quote_id, item_name, item_description, quantity, unit_price, total_price)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            quote_id,
            "测试项目",
            "用于测试拒绝重新提交流程",
            1,
            1000.00,
            1000.00
        ))

        # 添加一条拒绝记录
        cursor.execute('''
            INSERT INTO approval_records
            (quote_id, action, status, comments, created_at, operation_channel)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            quote_id,
            "reject",
            "completed",
            "模拟拒绝，用于测试重新提交流程",
            datetime.utcnow(),
            "internal"
        ))

        conn.commit()

        print(f"✅ 创建成功: {quote_number} (ID: {quote_id})，状态: rejected")

        # 现在使用审批引擎测试重新提交
        db_gen = get_db()
        db: Session = next(db_gen)

        engine = UnifiedApprovalEngine(db)

        print(f"\n🚀 测试重新提交审批...")
        operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote_id,
            operator_id=1,
            channel=OperationChannel.INTERNAL,
            reason="被拒绝后重新提交审批测试"
        )

        result = engine.execute_operation(operation)

        print(f"重新提交结果:")
        print(f"   - 成功: {result.success}")
        print(f"   - 消息: {result.message}")
        print(f"   - 新状态: {result.new_status}")
        print(f"   - 审批方法: {result.approval_method}")
        print(f"   - 审批ID: {result.approval_id}")

        # 查看更新后的报价单状态
        cursor.execute('SELECT status, approval_status, wecom_approval_id FROM quotes WHERE id = ?', (quote_id,))
        result_status = cursor.fetchone()
        if result_status:
            print(f"\n📋 重新提交后报价单状态:")
            print(f"   - 状态: {result_status[0]}")
            print(f"   - 审批状态: {result_status[1]}")
            print(f"   - 企业微信审批ID: {result_status[2]}")

        # 查看审批记录
        print(f"\n📜 审批记录:")
        cursor.execute('''
            SELECT action, status, wecom_sp_no, created_at, comments
            FROM approval_records
            WHERE quote_id = ?
            ORDER BY created_at ASC
        ''', (quote_id,))
        records = cursor.fetchall()
        for i, record in enumerate(records, 1):
            print(f"   {i}. 动作: {record[0]}, 状态: {record[1]}, 企业微信编号: {record[2]}, 时间: {record[3]}")
            if record[4]:
                print(f"      备注: {record[4]}")

        db.close()
        return quote_number

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return None

    finally:
        conn.close()

if __name__ == "__main__":
    quote_number = create_and_test_resubmit()
    if quote_number:
        print(f"\n🎉 测试完成！报价单号: {quote_number}")
        print(f"💡 检查企业微信是否收到重新提交的审批通知")
    else:
        print(f"\n❌ 测试失败")