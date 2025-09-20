#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from app.database import get_db
from app.models import Quote
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel
from app.services.unified_approval_service import ApprovalStatus

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_approval_engine_direct():
    """直接测试审批引擎"""
    print("🔧 直接测试审批引擎")
    print("=" * 50)

    # 获取数据库连接
    db = next(get_db())

    try:
        # 1. 重置报价单状态
        quote = db.query(Quote).filter(Quote.id == 12).first()
        if not quote:
            print("❌ 找不到报价单 ID 12")
            return False

        quote.status = 'draft'
        quote.approval_status = 'not_submitted'
        db.commit()
        db.refresh(quote)
        print(f"📊 初始状态: status={quote.status}, approval_status={quote.approval_status}")

        # 2. 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 3. 创建提交操作
        operation = ApprovalOperation(
            quote_id=12,
            action=ApprovalAction.SUBMIT,
            operator_id=1,  # 假设用户1是创建者
            channel=OperationChannel.INTERNAL,
            comments="测试提交审批"
        )

        print("\n🚀 执行提交审批操作")
        result = engine.execute_operation(operation)

        print(f"操作结果: success={result.success}")
        print(f"消息: {result.message}")
        print(f"新状态: {result.new_status}")

        # 4. 检查数据库状态
        db.refresh(quote)
        print(f"数据库状态: status={quote.status}, approval_status={quote.approval_status}")

        if result.success and quote.status == quote.approval_status:
            print("✅ 审批引擎测试成功！")
            return True
        else:
            print("❌ 审批引擎测试失败")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

if __name__ == "__main__":
    success = test_approval_engine_direct()
    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")