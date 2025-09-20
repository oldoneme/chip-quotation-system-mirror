#!/usr/bin/env python3

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database import get_db
from app.models import Quote

def reset_quote_status():
    """重置报价单状态为pending"""
    print("🔄 重置报价单状态")
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

        # 重置状态为pending
        quote.status = "pending"
        quote.approval_status = "pending"
        quote.rejection_reason = None
        quote.approved_at = None
        quote.approved_by = None

        db.commit()

        print(f"✅ 状态已重置为: pending")

    except Exception as e:
        print(f"❌ 重置异常: {e}")
        import traceback
        print(traceback.format_exc())
    finally:
        db.close()

if __name__ == "__main__":
    reset_quote_status()