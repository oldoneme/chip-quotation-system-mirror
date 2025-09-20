#!/usr/bin/env python3
"""
测试重新提交审批的企业微信通知问题
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from datetime import datetime
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel
from app.models import Quote

def test_resubmit_approval():
    print("🔍 测试重新提交审批流程")

    # 获取数据库连接
    db_gen = get_db()
    db: Session = next(db_gen)

    try:
        # 查找报价单 CIS-KS20250918012
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918012").first()
        if not quote:
            print("❌ 找不到报价单 CIS-KS20250918012")
            return

        print(f"📋 报价单信息:")
        print(f"   - ID: {quote.id}")
        print(f"   - 编号: {quote.quote_number}")
        print(f"   - 状态: {quote.status}")
        print(f"   - 审批状态: {quote.approval_status}")
        print(f"   - 企业微信审批ID: {quote.wecom_approval_id}")

        # 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 模拟重新提交操作
        operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=quote.id,
            operator_id=1,  # 假设用户ID为1
            channel=OperationChannel.INTERNAL,
            reason="重新提交审批测试",
            metadata={
                "timestamp": datetime.utcnow().isoformat()
            }
        )

        print(f"\n🚀 执行重新提交审批操作...")
        result = engine.execute_operation(operation)

        print(f"\n📊 操作结果:")
        print(f"   - 成功: {result.success}")
        print(f"   - 消息: {result.message}")
        print(f"   - 新状态: {result.new_status}")
        print(f"   - 审批方法: {result.approval_method}")
        print(f"   - 审批ID: {result.approval_id}")

        # 重新查询报价单状态
        db.refresh(quote)
        print(f"\n📋 操作后报价单状态:")
        print(f"   - 状态: {quote.status}")
        print(f"   - 审批状态: {quote.approval_status}")
        print(f"   - 企业微信审批ID: {quote.wecom_approval_id}")

        # 查看审批记录
        print(f"\n📜 查看最新审批记录:")
        import sqlite3
        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT ar.action, ar.status, ar.wecom_sp_no, ar.created_at
            FROM approval_records ar
            WHERE ar.quote_id = ?
            ORDER BY ar.created_at DESC
            LIMIT 3
        ''', (quote.id,))
        records = cursor.fetchall()
        for record in records:
            print(f"   - 动作: {record[0]}, 状态: {record[1]}, 企业微信编号: {record[2]}, 时间: {record[3]}")
        conn.close()

    except Exception as e:
        print(f"❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

    finally:
        db.close()

if __name__ == "__main__":
    test_resubmit_approval()