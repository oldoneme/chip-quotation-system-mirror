#!/usr/bin/env python3
"""
调试报价单CIS-KS20250918007的企业微信审批内容
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.models import Quote
from app.services.wecom_approval_service import WeComApprovalService

def debug_quote_007_content():
    """调试报价单007的审批内容"""
    print("🔍 调试报价单CIS-KS20250918007的审批内容")
    print("=" * 60)

    db = SessionLocal()
    try:
        # 获取报价单
        quote = db.query(Quote).filter(Quote.id == 21).first()
        if not quote:
            print("❌ 找不到报价单ID=21")
            return

        print(f"📋 报价单: {quote.quote_number}")
        print(f"💰 总金额: {quote.total_amount}")
        print(f"📝 描述: {quote.description}")
        print(f"📊 项目数量: {len(quote.items) if quote.items else 0}")

        # 构建审批数据
        service = WeComApprovalService(db)
        approval_data = service._build_approval_data(quote, 1)

        print("\n🔍 构建的审批数据:")
        import json
        print(json.dumps(approval_data, indent=2, ensure_ascii=False))

        # 特别检查Text-1756706160253控件的内容
        for content in approval_data["apply_data"]["contents"]:
            if content.get("id") == "Text-1756706160253":
                print(f"\n🎯 问题控件 Text-1756706160253 的内容:")
                print(f"📝 原始值: {repr(content['value']['text'])}")
                print(f"📝 显示值:")
                print(content['value']['text'])
                print(f"📏 字符长度: {len(content['value']['text'])}")
                break

    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_quote_007_content()