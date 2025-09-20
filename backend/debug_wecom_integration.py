#!/usr/bin/env python3
"""
调试企业微信集成问题
检查用户的userid字段和企业微信集成状态
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
from app.services.wecom_integration import WeComApprovalIntegration
from app.services.approval_engine import UnifiedApprovalEngine, ApprovalOperation, ApprovalAction, OperationChannel

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_database_users():
    """检查数据库中的用户信息"""
    print("🔍 检查数据库中的用户信息")
    print("=" * 50)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 查询所有用户
        users = db.query(User).all()
        print(f"总用户数: {len(users)}")

        for user in users:
            print(f"用户ID: {user.id}")
            print(f"  用户名: {user.name}")
            print(f"  角色: {user.role}")
            print(f"  企业微信ID: {user.userid or '无'}")
            print(f"  创建时间: {user.created_at}")
            print("-" * 30)

        # 查询最近的报价单
        recent_quotes = db.query(Quote).order_by(Quote.created_at.desc()).limit(5).all()
        print(f"\n📋 最近5个报价单:")
        for quote in recent_quotes:
            creator = db.query(User).filter(User.id == quote.created_by).first() if quote.created_by else None
            print(f"报价单 {quote.id}: {quote.quote_number}")
            print(f"  创建者ID: {quote.created_by}")
            print(f"  创建者: {creator.name if creator else '未知'}")
            print(f"  创建者企业微信ID: {creator.userid if creator and creator.userid else '无'}")
            print(f"  状态: {quote.status}")
            print(f"  企业微信审批ID: {quote.wecom_approval_id or '无'}")
            print("-" * 30)

    finally:
        db.close()

def test_wecom_integration():
    """测试企业微信集成"""
    print("🧪 测试企业微信集成")
    print("=" * 50)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 初始化企业微信集成服务
        wecom_service = WeComApprovalIntegration(db)

        # 检查配置
        print("企业微信配置检查:")
        print(f"  Corp ID: {getattr(wecom_service, 'corp_id', '未设置')}")
        print(f"  Agent ID: {getattr(wecom_service, 'agent_id', '未设置')}")
        print(f"  模板ID: {getattr(wecom_service, 'approval_template_id', '未设置')}")

        # 查找一个草稿状态的报价单进行测试（确保未被软删除）
        draft_quote = db.query(Quote).filter(
            Quote.status == 'draft',
            Quote.is_deleted == False
        ).first()
        if draft_quote:
            print(f"\n找到草稿报价单: {draft_quote.id} - {draft_quote.quote_number}")

            # 检查创建者信息
            creator = db.query(User).filter(User.id == draft_quote.created_by).first() if draft_quote.created_by else None
            if creator:
                print(f"创建者: {creator.name}")
                print(f"企业微信ID: {creator.userid or '无'}")

                # 如果创建者没有企业微信ID，添加一个测试用的
                if not creator.userid:
                    print("⚠️ 创建者缺少企业微信ID，添加测试ID...")
                    creator.userid = "test_userid_001"
                    db.commit()
                    print(f"✅ 已设置企业微信ID: {creator.userid}")
            else:
                print("❌ 未找到创建者")
        else:
            print("❌ 未找到草稿状态的报价单")

    finally:
        db.close()

async def test_submit_approval():
    """测试提交审批"""
    print("🚀 测试提交审批流程")
    print("=" * 50)

    # 创建数据库连接
    engine = create_engine('sqlite:///app/test.db')
    Session = sessionmaker(bind=engine)
    db = Session()

    try:
        # 查找一个草稿状态的报价单（确保未被软删除）
        draft_quote = db.query(Quote).filter(
            Quote.status == 'draft',
            Quote.is_deleted == False
        ).first()
        if not draft_quote:
            print("❌ 未找到草稿状态的报价单")
            return

        print(f"使用报价单: {draft_quote.id} - {draft_quote.quote_number}")

        # 初始化统一审批引擎
        approval_engine = UnifiedApprovalEngine(db)

        # 创建审批操作
        operation = ApprovalOperation(
            action=ApprovalAction.SUBMIT,
            quote_id=draft_quote.id,
            operator_id=draft_quote.created_by,
            channel=OperationChannel.INTERNAL,
            comments="测试企业微信集成调试"
        )

        print("开始执行审批操作...")
        result = approval_engine.execute_operation(operation)

        print(f"操作结果:")
        print(f"  成功: {result.success}")
        print(f"  消息: {result.message}")
        print(f"  新状态: {result.new_status}")
        print(f"  审批方法: {result.approval_method}")
        print(f"  需要同步: {result.sync_required}")

    except Exception as e:
        print(f"❌ 测试失败: {e}")
        logger.exception("详细错误信息:")

    finally:
        db.close()

def main():
    """主函数"""
    print("🔧 企业微信集成调试工具")
    print("=" * 60)

    try:
        # 检查用户数据
        check_database_users()

        print("\n" + "=" * 60)

        # 测试企业微信集成
        test_wecom_integration()

        print("\n" + "=" * 60)

        # 测试提交审批
        asyncio.run(test_submit_approval())

    except Exception as e:
        print(f"❌ 调试失败: {e}")
        logger.exception("详细错误信息:")

if __name__ == "__main__":
    main()