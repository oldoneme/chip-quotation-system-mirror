#!/usr/bin/env python3
"""
直接修复CIS-KS20250918007的数据
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Quote

def fix_quote_007():
    """修复报价单007"""
    print("🔧 修复报价单CIS-KS20250918007")
    print("=" * 60)

    db = SessionLocal()
    try:
        quote = db.query(Quote).filter(Quote.id == 21).first()
        if not quote:
            print("❌ 找不到报价单ID=21")
            return

        print(f"📋 当前报价单: {quote.quote_number}")
        print(f"💰 总金额: {quote.total_amount}")
        print(f"📝 描述: {quote.description}")

        # 检查报价单项目
        if quote.items:
            print(f"📊 项目数量: {len(quote.items)}")
            for i, item in enumerate(quote.items):
                print(f"   项目{i+1}: {item.item_name} - {item.quantity}{item.unit}")

        # 简化描述，移除可能有问题的字符
        if quote.description and len(quote.description) > 50:
            old_description = quote.description
            # 保持中文，只是简化内容
            quote.description = "项目CCA101芯片封装BGA256测试类型mixed"
            print(f"🔧 简化描述:")
            print(f"   旧: {old_description}")
            print(f"   新: {quote.description}")

        # 重置企业微信相关状态
        if quote.wecom_approval_id:
            print(f"🔧 重置企业微信审批ID: {quote.wecom_approval_id} -> None")
            quote.wecom_approval_id = None

        # 重置状态为草稿，这样可以重新提交
        if quote.status != 'draft':
            print(f"🔧 重置状态: {quote.status} -> draft")
            quote.status = 'draft'

        if quote.approval_status != 'not_submitted':
            print(f"🔧 重置审批状态: {quote.approval_status} -> not_submitted")
            quote.approval_status = 'not_submitted'

        # 提交更改
        db.commit()
        print("✅ 修复完成")

        # 验证修复
        db.refresh(quote)
        print(f"📊 修复后状态:")
        print(f"   状态: {quote.status}")
        print(f"   审批状态: {quote.approval_status}")
        print(f"   企业微信ID: {quote.wecom_approval_id}")
        print(f"   描述: {quote.description}")

    except Exception as e:
        print(f"❌ 修复失败: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    fix_quote_007()