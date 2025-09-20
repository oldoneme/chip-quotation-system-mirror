#!/usr/bin/env python3
"""
测试SQLAlchemy session修复后的企业微信集成
创建测试报价单并验证提交操作
"""

import sys
import os
import asyncio
import logging
from datetime import datetime
import uuid

# 添加应用路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Quote, User
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_session_fix():
    """测试SQLAlchemy session修复"""
    print("🚀 测试SQLAlchemy session修复后的企业微信集成")
    print("=" * 60)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 查找或创建测试用户
        test_user = db.query(User).filter(User.name == "测试用户").first()
        if not test_user:
            print("创建测试用户...")
            test_user = User(
                name="测试用户",
                email="test@example.com",
                role="user",
                userid="testuser001"  # 企业微信用户ID
            )
            db.add(test_user)
            db.commit()
            print(f"✅ 创建测试用户: {test_user.id}")
        else:
            print(f"✅ 找到测试用户: {test_user.id} - {test_user.name}")

        # 创建测试报价单
        test_quote_number = f"SESSION-FIX-TEST-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        test_quote = Quote(
            quote_number=test_quote_number,
            title="Session修复测试项目",
            customer_name="测试客户",
            status="draft",
            approval_status="draft",
            created_by=test_user.id,
            created_at=datetime.utcnow(),
            is_deleted=False
        )

        db.add(test_quote)
        db.commit()
        print(f"✅ 创建测试报价单: {test_quote.id} - {test_quote.quote_number}")

        # 初始化统一审批引擎
        approval_engine = UnifiedApprovalEngine(db)

        # 创建提交审批操作
        operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=test_quote.id,
            operator_id=test_user.id,
            channel=OperationChannel.INTERNAL,
            comments="测试SQLAlchemy session修复"
        )

        print(f"\n🔄 执行提交审批操作...")
        print(f"   操作: {operation.action}")
        print(f"   渠道: {operation.channel}")
        print(f"   操作者: {test_user.name}")
        print(f"   企业微信ID: {test_user.userid}")

        # 执行操作
        result = approval_engine.execute_operation(operation)

        print(f"\n📊 操作结果:")
        print(f"   成功: {result.success}")
        print(f"   消息: {result.message}")
        print(f"   新状态: {result.new_status}")
        print(f"   审批方法: {result.approval_method}")
        print(f"   需要同步: {result.sync_required}")

        # 刷新报价单数据检查结果
        db.refresh(test_quote)
        print(f"\n📝 提交后状态:")
        print(f"   报价单状态: {test_quote.status}")
        print(f"   审批状态: {test_quote.approval_status}")
        print(f"   提交时间: {test_quote.submitted_at}")
        print(f"   提交者: {test_quote.submitted_by}")

        # 分析结果
        print(f"\n📈 分析:")
        if result.success:
            print("   ✅ 操作成功完成")
            print("   ✅ SQLAlchemy session问题已修复")
            if result.approval_method.value == 'wecom':
                print("   ✅ 标记为企业微信审批")
            if result.sync_required:
                print("   ✅ 标记需要同步")
        else:
            print("   ❌ 操作失败")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.exception("详细错误信息:")

    finally:
        db.close()

def main():
    """主函数"""
    try:
        test_session_fix()
    except Exception as e:
        print(f"❌ 总体测试失败: {e}")
        logger.exception("详细错误信息:")

if __name__ == "__main__":
    main()