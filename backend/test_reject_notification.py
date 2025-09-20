#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import asyncio
from app.database import get_db
from app.models import Quote, User
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

async def test_reject_notification():
    """测试拒绝通知功能"""
    print("🧪 测试拒绝通知功能")
    print("=" * 50)

    db = next(get_db())

    try:
        # 查询CIS-KS20250918001报价单
        quote = db.query(Quote).filter(Quote.quote_number == "CIS-KS20250918001").first()
        if not quote:
            print("❌ 找不到报价单 CIS-KS20250918001")
            return

        print(f"📋 报价单: {quote.quote_number}")
        print(f"📊 当前状态: {quote.status}")
        print(f"📊 创建者ID: {quote.created_by}")

        # 查询创建者信息
        creator = db.query(User).filter(User.id == quote.created_by).first()
        if not creator:
            print("❌ 找不到创建者")
            return

        print(f"👤 创建者: {creator.name} ({creator.userid})")

        # 如果报价单已经是拒绝状态，先改回pending状态进行测试
        if quote.status == "rejected":
            print("🔄 报价单已被拒绝，重置为pending状态进行测试")
            quote.status = "pending"
            quote.approval_status = "pending"
            db.commit()

        # 创建审批引擎
        approval_engine = UnifiedApprovalEngine(db)

        # 创建拒绝操作
        reject_operation = ApprovalOperation(
            quote_id=quote.id,
            action=ApprovalAction.REJECT,
            operator_id=1,  # 假设管理员ID为1
            reason="测试拒绝通知功能",
            comments="这是一个测试拒绝",
            channel=OperationChannel.INTERNAL
        )

        print(f"🚀 执行拒绝操作...")
        result = approval_engine.execute_operation(reject_operation)

        if result.success:
            print(f"✅ 拒绝操作成功: {result.message}")
            print(f"📊 新状态: {result.new_status.value}")

            # 检查企业微信通知是否已发送
            print("⏳ 等待通知发送...")
            await asyncio.sleep(3)  # 等待3秒

            print("✅ 拒绝通知应该已经发送")
        else:
            print(f"❌ 拒绝操作失败: {result.message}")

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(test_reject_notification())