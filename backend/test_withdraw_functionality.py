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

def test_withdraw_functionality():
    """测试撤回功能"""
    print("🔧 测试撤回功能")
    print("=" * 50)

    # 获取数据库连接
    db = next(get_db())

    try:
        # 1. 重置报价单状态为pending
        quote = db.query(Quote).filter(Quote.id == 12).first()
        if not quote:
            print("❌ 找不到报价单 ID 12")
            return False

        quote.status = 'pending'
        quote.approval_status = 'pending'
        db.commit()
        db.refresh(quote)
        print(f"📊 初始状态: status={quote.status}, approval_status={quote.approval_status}")

        # 2. 创建审批引擎
        engine = UnifiedApprovalEngine(db)

        # 3. 测试撤回操作
        operation = ApprovalOperation(
            quote_id=12,
            action=ApprovalAction.WITHDRAW,
            operator_id=1,  # 假设用户1是创建者
            channel=OperationChannel.INTERNAL,
            comments="测试撤回审批"
        )

        print("\n🚀 执行撤回操作")
        result = engine.execute_operation(operation)

        print(f"操作结果: success={result.success}")
        print(f"消息: {result.message}")
        print(f"新状态: {result.new_status}")

        # 4. 检查数据库状态
        db.refresh(quote)
        print(f"数据库状态: status={quote.status}, approval_status={quote.approval_status}")

        # 5. 验证状态是否回到草稿状态
        expected_status = "draft"
        expected_approval_status = "not_submitted"

        if (result.success and
            quote.status == expected_status and
            quote.approval_status == expected_approval_status):
            print("✅ 撤回功能测试成功！")
            print(f"   状态已从 pending -> {expected_status}")
            print(f"   审批状态已从 pending -> {expected_approval_status}")
            return True
        else:
            print("❌ 撤回功能测试失败")
            print(f"   期望状态: {expected_status}, 实际: {quote.status}")
            print(f"   期望审批状态: {expected_approval_status}, 实际: {quote.approval_status}")
            return False

    except Exception as e:
        print(f"❌ 测试异常: {e}")
        import traceback
        print(traceback.format_exc())
        return False
    finally:
        db.close()

def test_withdraw_permission():
    """测试撤回权限 - 非创建者不能撤回"""
    print("\n🔧 测试撤回权限")
    print("=" * 50)

    db = next(get_db())

    try:
        # 确保报价单状态为pending
        quote = db.query(Quote).filter(Quote.id == 12).first()
        quote.status = 'pending'
        quote.approval_status = 'pending'
        db.commit()

        engine = UnifiedApprovalEngine(db)

        # 使用不同的用户ID（非创建者，但用户存在）
        operation = ApprovalOperation(
            quote_id=12,
            action=ApprovalAction.WITHDRAW,
            operator_id=7,  # 李亮 - 非创建者
            channel=OperationChannel.INTERNAL,
            comments="非法撤回测试"
        )

        print("🚀 测试非创建者撤回（应该失败）")
        result = engine.execute_operation(operation)

        if not result.success and "只有创建者可以撤回" in result.message:
            print("✅ 撤回权限控制正常")
            return True
        else:
            print("❌ 撤回权限控制失败")
            return False

    except Exception as e:
        print(f"权限测试异常: {e}")
        return False
    finally:
        db.close()

if __name__ == "__main__":
    print("🎯 开始撤回功能完整测试")

    success1 = test_withdraw_functionality()
    success2 = test_withdraw_permission()

    overall_success = success1 and success2
    print(f"\n🎯 整体测试结果: {'成功' if overall_success else '失败'}")

    if overall_success:
        print("\n🎉 撤回功能已完全实现并测试通过！")
        print("✅ 创建者可以在'待审批'状态下撤回到'草稿'状态")
        print("✅ 非创建者无法执行撤回操作")
        print("✅ 状态同步正常工作")