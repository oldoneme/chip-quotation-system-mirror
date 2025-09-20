#!/usr/bin/env python3
"""
专门测试企业微信审批ID保存问题
"""

import asyncio
import sys
import os
import uuid
from datetime import datetime
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from sqlalchemy.orm import sessionmaker
from app.database import engine
from app.services.approval_engine import UnifiedApprovalEngine
from app.services.wecom_integration import WeComApprovalIntegration
from app.models import Quote, User
import sqlite3

SessionLocal = sessionmaker(bind=engine)

async def test_wecom_approval_id_saving():
    """测试企业微信审批ID保存功能"""
    print("=== 企业微信审批ID保存测试 ===\n")

    db = SessionLocal()

    try:
        # 1. 创建测试报价单
        print("1. 创建测试报价单...")
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

        new_quote = Quote(
            quote_number=f"WECOM-ID-TEST-{timestamp}-{unique_id}",
            title="企业微信审批ID测试",
            customer_name="测试客户",
            customer_contact="测试联系人",
            total_amount=25000.00,
            approval_status="not_submitted",
            approval_method="internal",
            created_by=1,
            status="active"
        )
        db.add(new_quote)
        db.commit()
        db.refresh(new_quote)
        quote_id = new_quote.id
        print(f"   ✅ 创建报价单: {new_quote.quote_number} (ID: {quote_id})")

        # 2. 直接调用企业微信集成服务
        print("\n2. 直接调用企业微信集成服务...")
        wecom_integration = WeComApprovalIntegration(db)

        # 模拟提交企业微信审批
        result = await wecom_integration.submit_quote_approval(quote_id, creator_userid="test_user")
        print(f"   企业微信审批提交结果: {result}")

        # 3. 检查WeChat approval ID是否保存
        print("\n3. 检查WeChat approval ID保存情况...")
        db.refresh(new_quote)
        print(f"   提交后WeChat审批ID: {new_quote.wecom_approval_id}")
        print(f"   提交后审批方法: {new_quote.approval_method}")

        if new_quote.wecom_approval_id:
            print("   ✅ WeChat审批ID已成功保存")

            # 4. 测试统一审批引擎中的保存逻辑
            print("\n4. 测试统一审批引擎中的WeChat ID保存逻辑...")

            # 模拟统一审批引擎保存逻辑
            approval_engine = UnifiedApprovalEngine(db)
            test_sp_no = f"TEST-SP-{datetime.now().strftime('%Y%m%d%H%M%S')}"

            # 直接更新数据库
            fresh_quote = db.query(Quote).filter(Quote.id == quote_id).first()
            if fresh_quote:
                fresh_quote.wecom_approval_id = test_sp_no
                fresh_quote.approval_method = 'wecom'
                db.commit()
                print(f"   ✅ 手动保存测试SP号: {test_sp_no}")

                # 验证保存
                db.refresh(fresh_quote)
                print(f"   验证保存结果: WeChat ID = {fresh_quote.wecom_approval_id}")

        else:
            print("   ❌ WeChat审批ID未保存")

        # 5. 检查数据库直接操作
        print("\n5. 数据库直接操作验证...")
        conn = sqlite3.connect('app/test.db')
        cursor = conn.cursor()

        cursor.execute('SELECT quote_number, approval_method, wecom_approval_id FROM quotes WHERE id = ?', (quote_id,))
        db_result = cursor.fetchone()

        if db_result:
            print(f"   数据库直接查询: {db_result}")

        conn.close()

        return new_quote.wecom_approval_id is not None

    except Exception as e:
        print(f"❌ 测试过程中出现错误: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()

async def main():
    """主函数"""
    print("启动企业微信审批ID保存专项测试...\n")

    success = await test_wecom_approval_id_saving()

    print(f"\n=== 测试完成 ===")
    print(f"结果: {'✅ 通过' if success else '❌ 失败'}")

    return success

if __name__ == "__main__":
    result = asyncio.run(main())
    sys.exit(0 if result else 1)