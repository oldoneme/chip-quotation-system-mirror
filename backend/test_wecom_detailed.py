#!/usr/bin/env python3
"""
详细测试企业微信集成
使用现有的pending报价单测试企业微信集成
"""

import sys
import os
import asyncio
import logging

# 添加应用路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Quote, User
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_wecom_with_pending_quote():
    """使用pending状态的报价单测试企业微信集成"""
    print("🔧 测试企业微信集成 - 使用pending报价单")
    print("=" * 60)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 查找pending状态的报价单
        pending_quote = db.query(Quote).filter(
            Quote.status == 'pending',
            Quote.is_deleted == False
        ).first()

        if not pending_quote:
            print("❌ 未找到pending状态的报价单")
            return

        print(f"使用报价单: {pending_quote.id} - {pending_quote.quote_number}")

        # 检查创建者信息
        creator = db.query(User).filter(User.id == pending_quote.created_by).first() if pending_quote.created_by else None
        if creator:
            print(f"创建者: {creator.name}")
            print(f"企业微信ID: {creator.userid or '无'}")
        else:
            print("❌ 未找到创建者")
            return

        # 模拟再次提交这个报价单（虽然它已经是pending状态）
        # 这将触发我们的详细日志
        print("\n🚀 模拟提交操作来测试企业微信集成...")

        # 初始化统一审批引擎
        approval_engine = UnifiedApprovalEngine(db)

        # 创建审批操作 - 使用APPROVE操作，因为quote已经是pending状态
        operation = ApprovalOperation(
            action=ApprovalAction.APPROVE,  # 改为批准操作
            quote_id=pending_quote.id,
            operator_id=creator.id,  # 使用创建者作为操作者
            channel=OperationChannel.INTERNAL,
            comments="测试企业微信集成 - 批准操作"
        )

        print("执行批准操作...")
        result = approval_engine.execute_operation(operation)

        print(f"\n操作结果:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")
        print(f"  新状态: {result.new_status}")
        print(f"  审批方法: {result.approval_method}")
        print(f"  需要同步: {result.sync_required}")

        # 检查报价单是否有企业微信审批ID
        db.refresh(pending_quote)
        print(f"\n审批后状态:")
        print(f"  报价单状态: {pending_quote.status}")
        print(f"  企业微信审批ID: {pending_quote.wecom_approval_id or '无'}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.exception("详细错误信息:")

    finally:
        db.close()

def test_wecom_direct_call():
    """直接测试企业微信集成服务"""
    print("\n🧪 直接测试企业微信集成服务")
    print("=" * 60)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        from app.services.wecom_integration import WeComApprovalIntegration

        # 查找pending状态的报价单
        pending_quote = db.query(Quote).filter(
            Quote.status == 'pending',
            Quote.is_deleted == False
        ).first()

        if not pending_quote:
            print("❌ 未找到pending状态的报价单")
            return

        print(f"使用报价单: {pending_quote.id} - {pending_quote.quote_number}")

        # 直接调用企业微信集成服务
        wecom_service = WeComApprovalIntegration(db)

        print("📞 直接调用 submit_quote_approval...")

        async def test_async():
            try:
                result = await wecom_service.submit_quote_approval(pending_quote.id)
                print(f"✅ 企业微信调用成功: {result}")
                return result
            except Exception as e:
                print(f"❌ 企业微信调用失败: {e}")
                logger.exception("详细错误信息:")
                return None

        result = asyncio.run(test_async())

        # 检查结果
        if result:
            print(f"提交结果: {result}")

            # 刷新报价单数据
            db.refresh(pending_quote)
            print(f"企业微信审批ID: {pending_quote.wecom_approval_id or '无'}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.exception("详细错误信息:")

    finally:
        db.close()

def main():
    """主函数"""
    try:
        # 测试通过审批引擎
        test_wecom_with_pending_quote()

        # 直接测试企业微信服务
        test_wecom_direct_call()

    except Exception as e:
        print(f"❌ 总体测试失败: {e}")
        logger.exception("详细错误信息:")

if __name__ == "__main__":
    main()