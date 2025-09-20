#!/usr/bin/env python3
"""
测试提交审批的企业微信集成
使用新创建的draft报价单测试提交操作
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

def test_submit_wecom_integration():
    """测试提交审批的企业微信集成"""
    print("🚀 测试提交审批的企业微信集成")
    print("=" * 60)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 查找我们刚创建的draft报价单
        draft_quote = db.query(Quote).filter(
            Quote.quote_number == 'TEST-WECOM-FIX-001',
            Quote.status == 'draft',
            Quote.is_deleted == False
        ).first()

        if not draft_quote:
            print("❌ 未找到测试报价单 TEST-WECOM-FIX-001")
            return

        print(f"✅ 找到测试报价单: {draft_quote.id} - {draft_quote.quote_number}")

        # 检查创建者信息
        creator = db.query(User).filter(User.id == draft_quote.created_by).first()
        if creator:
            print(f"📋 创建者: {creator.name}")
            print(f"📋 企业微信ID: {creator.userid}")
        else:
            print("❌ 未找到创建者")
            return

        print(f"\n📝 当前状态:")
        print(f"   报价单状态: {draft_quote.status}")
        print(f"   审批状态: {draft_quote.approval_status}")
        print(f"   企业微信审批ID: {draft_quote.wecom_approval_id or '无'}")

        # 初始化统一审批引擎
        approval_engine = UnifiedApprovalEngine(db)

        # 创建提交审批操作
        operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,  # 关键：使用SUBMIT操作
            quote_id=draft_quote.id,
            operator_id=creator.id,
            channel=OperationChannel.INTERNAL,  # 内部操作应该触发企业微信
            comments="测试企业微信集成 - 提交审批"
        )

        print(f"\n🔄 执行提交审批操作...")
        print(f"   操作: {operation.action}")
        print(f"   渠道: {operation.channel}")
        print(f"   操作者: {creator.name}")

        # 执行操作
        result = approval_engine.execute_operation(operation)

        print(f"\n📊 操作结果:")
        print(f"   成功: {result.success}")
        print(f"   消息: {result.message}")
        print(f"   新状态: {result.new_status}")
        print(f"   审批方法: {result.approval_method}")
        print(f"   需要同步: {result.sync_required}")
        print(f"   操作ID: {getattr(result, 'operation_id', '无')}")

        # 刷新报价单数据检查结果
        db.refresh(draft_quote)
        print(f"\n📝 提交后状态:")
        print(f"   报价单状态: {draft_quote.status}")
        print(f"   审批状态: {draft_quote.approval_status}")
        print(f"   企业微信审批ID: {draft_quote.wecom_approval_id or '无'}")
        print(f"   提交时间: {draft_quote.submitted_at}")
        print(f"   提交者: {draft_quote.submitted_by}")

        # 分析结果
        print(f"\n📈 分析:")
        if result.success:
            if result.approval_method.value == 'wecom':
                print("   ✅ 操作成功，标记为企业微信审批")
            else:
                print("   ⚠️ 操作成功，但标记为内部审批")

            if result.sync_required:
                print("   ✅ 标记需要同步")
            else:
                print("   ⚠️ 未标记需要同步")

            if draft_quote.wecom_approval_id:
                print("   ✅ 企业微信审批ID已设置")
            else:
                print("   ❌ 企业微信审批ID未设置")
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
        test_submit_wecom_integration()
    except Exception as e:
        print(f"❌ 总体测试失败: {e}")
        logger.exception("详细错误信息:")

if __name__ == "__main__":
    main()