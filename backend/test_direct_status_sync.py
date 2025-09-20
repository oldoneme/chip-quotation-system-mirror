#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from app.database import get_db
from app.models import Quote
from app.services.approval_status_synchronizer import ApprovalStatusSynchronizer
from app.services.unified_approval_service import ApprovalStatus

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

def test_direct_status_sync():
    """直接测试状态同步器"""
    print("🔧 直接测试状态同步器")
    print("=" * 50)

    # 获取数据库连接
    db = next(get_db())

    try:
        # 1. 选择一个报价单进行测试
        quote = db.query(Quote).filter(Quote.id == 12).first()
        if not quote:
            print("❌ 找不到报价单 ID 12")
            return False

        print(f"📊 测试报价单: ID={quote.id}, Number={quote.quote_number}")
        print(f"初始状态: status={quote.status}, approval_status={quote.approval_status}")

        # 2. 重置为一致状态
        quote.status = 'draft'
        quote.approval_status = 'not_submitted'
        db.commit()
        db.refresh(quote)
        print(f"重置后状态: status={quote.status}, approval_status={quote.approval_status}")

        # 3. 创建状态同步器
        synchronizer = ApprovalStatusSynchronizer(db)

        # 4. 测试同步到 pending 状态
        print("\n🚀 测试同步到 pending 状态")
        success = synchronizer.sync_status_fields(quote.id, ApprovalStatus.PENDING)
        print(f"同步操作结果: {success}")

        # 5. 验证结果
        db.refresh(quote)
        print(f"同步后状态: status={quote.status}, approval_status={quote.approval_status}")

        # 6. 检查一致性
        is_consistent, message = synchronizer.check_status_consistency(quote.id)
        print(f"一致性检查: {is_consistent} - {message}")

        if is_consistent and quote.status == "pending" and quote.approval_status == "pending":
            print("✅ 状态同步测试成功！")
            return True
        else:
            print("❌ 状态同步测试失败")
            return False

    finally:
        db.close()

if __name__ == "__main__":
    success = test_direct_status_sync()
    print(f"\n🎯 测试结果: {'成功' if success else '失败'}")